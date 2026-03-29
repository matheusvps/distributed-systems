const readline = require("readline/promises");
const { stdin: input, stdout: output } = require("process");
const { createEventEnvelope } = require("../shared/events");
const { signEvent, verifyEvent } = require("../shared/signature");
const { createLogger } = require("../shared/logger");
const { createRabbitChannel, publish, subscribe } = require("../shared/rabbit");
const {
  EVENTS_EXCHANGE,
  ROUTING_KEYS,
  QUEUES
} = require("../shared/constants");

const SERVICE_NAME = "gateway";
const logger = createLogger("MS Gateway");
const promotions = new Map();

function slugifyCategory(category) {
  return String(category || "geral")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-");
}

function printPromotions() {
  if (promotions.size === 0) {
    console.log("\nNenhuma promocao validada ainda.\n");
    return;
  }

  console.log("\nPromocoes validadas:");
  for (const promo of promotions.values()) {
    console.log(
      `- ID: ${promo.id} | Titulo: ${promo.title} | Categoria: ${promo.category} | Preco: R$ ${promo.price}`
    );
  }
  console.log("");
}

async function publishSignedEvent(channel, routingKey, payload) {
  const event = createEventEnvelope(routingKey, SERVICE_NAME, payload);
  event.signature = signEvent(event, SERVICE_NAME);
  publish(channel, EVENTS_EXCHANGE, routingKey, event);
}

async function start() {
  const { connection, channel } = await createRabbitChannel(logger);

  await subscribe({
    channel,
    queue: QUEUES.GATEWAY,
    exchange: EVENTS_EXCHANGE,
    routingKeys: [ROUTING_KEYS.PROMOCAO_PUBLICADA],
    logger,
    onMessage: async (event) => {
      if (!verifyEvent(event)) {
        logger.warn("Evento promocao.publicada descartado por assinatura invalida.");
        return;
      }

      const promo = event.payload;
      promotions.set(promo.id, promo);
      logger.info(`Promocao validada recebida: ${promo.id} - ${promo.title}`);
    }
  });

  logger.info("Gateway iniciado. Consumindo promocoes validadas...");

  const rl = readline.createInterface({ input, output });

  while (true) {
    console.log("\n=== Menu Gateway ===");
    console.log("1) Cadastrar nova promocao");
    console.log("2) Listar promocoes validadas");
    console.log("3) Votar em promocao");
    console.log("4) Sair");

    const option = (await rl.question("Escolha uma opcao: ")).trim();

    if (option === "1") {
      const title = (await rl.question("Titulo da promocao: ")).trim();
      const category = slugifyCategory(await rl.question("Categoria (ex: livro, jogo): "));
      const priceRaw = (await rl.question("Preco: ")).trim();
      const store = (await rl.question("Loja: ")).trim();

      const payload = {
        id: crypto.randomUUID(),
        title,
        category,
        price: Number(priceRaw),
        store,
        createdAt: new Date().toISOString()
      };

      await publishSignedEvent(channel, ROUTING_KEYS.PROMOCAO_RECEBIDA, payload);
      logger.info(`Evento ${ROUTING_KEYS.PROMOCAO_RECEBIDA} publicado (${payload.id}).`);
    } else if (option === "2") {
      printPromotions();
    } else if (option === "3") {
      if (promotions.size === 0) {
        console.log("\nNenhuma promocao disponivel para voto.\n");
        continue;
      }

      printPromotions();
      const promotionId = (await rl.question("Digite o ID da promocao: ")).trim();
      const voteRaw = (await rl.question("Voto (+1 para positivo, -1 para negativo): ")).trim();
      const vote = Number(voteRaw);

      if (![1, -1].includes(vote)) {
        console.log("Voto invalido. Use +1 ou -1.");
        continue;
      }

      const promotion = promotions.get(promotionId);
      if (!promotion) {
        console.log("Promocao nao encontrada na lista validada.");
        continue;
      }

      const payload = {
        promotionId,
        vote,
        votedAt: new Date().toISOString(),
        promotion
      };

      await publishSignedEvent(channel, ROUTING_KEYS.PROMOCAO_VOTO, payload);
      logger.info(`Evento ${ROUTING_KEYS.PROMOCAO_VOTO} publicado para ${promotionId}.`);
    } else if (option === "4") {
      logger.info("Encerrando gateway...");
      await channel.close();
      await connection.close();
      rl.close();
      process.exit(0);
    } else {
      console.log("Opcao invalida.");
    }
  }
}

const crypto = require("crypto");

start().catch((error) => {
  logger.error(`Falha no gateway: ${error.message}`);
  process.exit(1);
});
