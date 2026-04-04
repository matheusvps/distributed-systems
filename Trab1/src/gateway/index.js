const readline = require("readline/promises");
const { stdin: input, stdout: output } = require("process");
const { createEventEnvelope } = require("../shared/events");
const { signEvent, verifyEvent } = require("../shared/signature");
const { createLogger } = require("../shared/logger");
const { createRabbitChannel, publish, subscribe } = require("../shared/rabbit");
const {
  EVENTS_EXCHANGE,
  ROUTING_KEYS,
  QUEUES,
  LOG_LEVELS
} = require("../shared/constants");
const { isPromotionValid, isVoteValid } = require("../shared/validation");
const config = require("../../config");

const SERVICE_NAME = "gateway";
process.env.SERVICE_NAME = SERVICE_NAME;
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
    return [];
  }

  console.log("\nPromocoes validadas:");
  const list = Array.from(promotions.values());
  list.forEach((promo, index) => {
    console.log(
      `[${index + 1}] ID: ${promo.id} | Titulo: ${promo.title} | Categoria: ${promo.category} | Preco: R$ ${promo.price}`
    );
  });
  console.log("");
  return list;
}

function printCategoryGrid() {
  const cats = config.categories || [];
  console.log("\nCategorias Disponiveis:");
  const columns = 3;
  for (let i = 0; i < cats.length; i += columns) {
    const row = cats.slice(i, i + columns)
      .map(c => `  [ ${c.padEnd(10)} ]`)
      .join("");
    console.log(row);
  }
}

async function publishSignedEvent(channel, routingKey, payload) {
  const event = createEventEnvelope(routingKey, SERVICE_NAME, payload);
  event.signature = signEvent(event, SERVICE_NAME);
  publish(channel, EVENTS_EXCHANGE, routingKey, event);
}

async function start() {
  const { connection, channel } = await createRabbitChannel(logger);

  function safeLog(message, level = LOG_LEVELS.INFO) {
    const timestamp = new Date().toISOString();
    const formatted = `[${timestamp}] [MS Gateway] [${level}] ${message}`;

    process.stdout.write(`\r\x1b[K${formatted}\n`);
  }

  await subscribe({
    channel,
    queue: QUEUES.GATEWAY,
    exchange: EVENTS_EXCHANGE,
    routingKeys: [ROUTING_KEYS.PROMOCAO_PUBLICADA],
    logger,
    onMessage: async (event) => {
      if (!verifyEvent(event)) {
        safeLog("Evento promocao.publicada descartado por assinatura invalida.", LOG_LEVELS.WARN);
        return;
      }

      const promo = event.payload;
      promotions.set(promo.id, promo);
      safeLog(`Promocao validada recebida: ${promo.id} - ${promo.title}`);

      if (pendingPublicacao.has(promo.id)) {
        const resolve = pendingPublicacao.get(promo.id);
        pendingPublicacao.delete(promo.id);
        resolve();
      }
    }
  });

  const pendingPublicacao = new Map();
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  safeLog("Gateway iniciado. Consumindo promocoes validadas...");

  const rl = readline.createInterface({ input, output });

  while (true) {
    await sleep(500);

    console.log("\n=== Menu Gateway ===");
    console.log("1) Cadastrar nova promocao");
    console.log("2) Listar promocoes validadas");
    console.log("3) Votar em promocao");
    console.log("4) Sair");

    const option = (await rl.question("Escolha uma opcao: ")).trim();

    if (option === "1") {
      const title = (await rl.question("Titulo da promocao: ")).trim();

      printCategoryGrid();
      const categoryRaw = (await rl.question("Escolha a Categoria: ")).trim();

      const category = slugifyCategory(categoryRaw);
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

      if (!isPromotionValid(payload)) {
        safeLog(`Dados da promocao invalidos. Escolha uma categoria da grade acima. Preco deve ser > 0.`, LOG_LEVELS.WARN);
        continue;
      }

      const waitForValidation = new Promise((resolve) => {
        pendingPublicacao.set(payload.id, resolve);
        setTimeout(() => {
          if (pendingPublicacao.has(payload.id)) {
            pendingPublicacao.delete(payload.id);
            resolve();
          }
        }, 3000);
      });

      await publishSignedEvent(channel, ROUTING_KEYS.PROMOCAO_RECEBIDA, payload);
      safeLog(`Evento ${ROUTING_KEYS.PROMOCAO_RECEBIDA} publicado (${payload.id}).`, LOG_LEVELS.INFO);

      await waitForValidation;
    } else if (option === "2") {
      printPromotions();
    } else if (option === "3") {
      if (promotions.size === 0) {
        console.log("\nNenhuma promocao disponivel para voto.\n");
        continue;
      }
      
      const list = printPromotions();
      const inputId = (await rl.question("Digite o Numero [N] ou ID da promocao: ")).trim();
      const voteRaw = (await rl.question("Voto (+1 para positivo, -1 para negativo): ")).trim();
      const vote = Number(voteRaw);

      let promotion;
      const index = parseInt(inputId) - 1;
      if (!isNaN(index) && list[index]) {
        promotion = list[index];
      } else {
        promotion = promotions.get(inputId);
      }

      if (!promotion) {
        console.log("Promocao nao encontrada na lista validada.");
        continue;
      }

      const payload = {
        promotionId: promotion.id,
        vote,
        votedAt: new Date().toISOString(),
        promotion
      };

      if (!isVoteValid(payload)) {
        safeLog("Voto invalido. Use +1 ou -1.", LOG_LEVELS.WARN);
        continue;
      }

      await publishSignedEvent(channel, ROUTING_KEYS.PROMOCAO_VOTO, payload);
      safeLog(`Evento ${ROUTING_KEYS.PROMOCAO_VOTO} publicado para ${promotion.id.substring(0, 8)}...`, LOG_LEVELS.INFO);
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
