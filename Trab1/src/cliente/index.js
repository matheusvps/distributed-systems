const { createLogger } = require("../shared/logger");
const { createRabbitChannel, subscribe } = require("../shared/rabbit");
const config = require("../../config");
const {
  NOTIFICATIONS_EXCHANGE,
  ROUTING_KEYS
} = require("../shared/constants");

const selectedProfile = process.argv[2] || config.defaultClientProfile;
const profileConfig = config.clientProfiles[selectedProfile];

if (!profileConfig) {
  const available = Object.keys(config.clientProfiles).join(", ");
  console.error(`Perfil de cliente invalido: ${selectedProfile}`);
  console.error(`Perfis disponiveis: ${available}`);
  process.exit(1);
}

const clientName = profileConfig.name;
const configuredInterests = profileConfig.interests;

const logger = createLogger(clientName);

function buildRoutingKey(interest) {
  if (interest === "destaque" || interest === ROUTING_KEYS.PROMOCAO_DESTAQUE) {
    return ROUTING_KEYS.PROMOCAO_DESTAQUE;
  }

  if (interest.startsWith("promocao.")) {
    return interest;
  }

  return `${ROUTING_KEYS.PROMOCAO_CATEGORIA_PREFIX}.${interest}`;
}

async function start() {
  const { channel } = await createRabbitChannel(logger);

  const routingKeys = [...new Set(configuredInterests.map(buildRoutingKey))];
  const queueName = `${clientName.toLowerCase().replace(/\s+/g, "_")}.${Date.now()}`;

  await subscribe({
    channel,
    queue: queueName,
    exchange: NOTIFICATIONS_EXCHANGE,
    routingKeys,
    logger,
    onMessage: async (event, routingKey) => {
      console.log("\n==========================================");
      console.log(`[${clientName}] Notificacao recebida`);
      console.log(`Routing key: ${routingKey}`);
      console.log(`Mensagem: ${event.payload?.message || "sem mensagem"}`);
      console.log(`Detalhes: ${JSON.stringify(event.payload)}`);
      console.log("==========================================\n");
    }
  });

  logger.info(`Cliente iniciado com interesses: ${routingKeys.join(", ")}`);
}

start().catch((error) => {
  logger.error(`Falha no cliente: ${error.message}`);
  process.exit(1);
});
