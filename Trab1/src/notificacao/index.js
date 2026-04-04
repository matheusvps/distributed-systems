const { createEventEnvelope } = require("../shared/events");
const { verifyEvent } = require("../shared/signature");
const { createLogger } = require("../shared/logger");
const { createRabbitChannel, publish, subscribe } = require("../shared/rabbit");
const {
  EVENTS_EXCHANGE,
  NOTIFICATIONS_EXCHANGE,
  ROUTING_KEYS,
  QUEUES
} = require("../shared/constants");

const SERVICE_NAME = "notificacao";
process.env.SERVICE_NAME = SERVICE_NAME;
const logger = createLogger("MS Notificacao");

function categoryRoutingKey(category) {
  return `${ROUTING_KEYS.PROMOCAO_CATEGORIA_PREFIX}.${String(category || "geral").toLowerCase()}`;
}

function publishNotification(channel, routingKey, payload) {
  const event = createEventEnvelope(routingKey, SERVICE_NAME, payload);
  publish(channel, NOTIFICATIONS_EXCHANGE, routingKey, event);
}

async function start() {
  const { channel } = await createRabbitChannel(logger);

  await subscribe({
    channel,
    queue: QUEUES.NOTIFICACAO,
    exchange: EVENTS_EXCHANGE,
    routingKeys: [ROUTING_KEYS.PROMOCAO_PUBLICADA, ROUTING_KEYS.PROMOCAO_DESTAQUE],
    logger,
    onMessage: async (event, routingKey) => {
      if (!verifyEvent(event)) {
        logger.warn(`Evento ${routingKey} descartado por assinatura invalida.`);
        return;
      }

      if (routingKey === ROUTING_KEYS.PROMOCAO_PUBLICADA) {
        const promo = event.payload;
        const categoryKey = categoryRoutingKey(promo.category);

        publishNotification(channel, categoryKey, {
          message: "Nova promocao publicada",
          promotionId: promo.id,
          title: promo.title,
          category: promo.category,
          price: promo.price,
          store: promo.store
        });

        logger.info(`Notificacao publicada em ${categoryKey} para promocao ${promo.id}.`);
        return;
      }

      if (routingKey === ROUTING_KEYS.PROMOCAO_DESTAQUE) {
        const promo = event.payload;
        const categoryKey = categoryRoutingKey(promo.category);

        publishNotification(channel, ROUTING_KEYS.PROMOCAO_DESTAQUE, {
          message: "Promocao em destaque (hot deal)",
          promotionId: promo.promotionId,
          title: promo.title,
          category: promo.category,
          score: promo.score,
          tag: "hot deal"
        });

        publishNotification(channel, categoryKey, {
          message: "hot deal",
          promotionId: promo.promotionId,
          title: promo.title,
          category: promo.category,
          score: promo.score,
          tag: "hot deal"
        });

        logger.info(`Notificacoes de destaque publicadas para ${promo.promotionId}.`);
      }
    }
  });

  logger.info("MS Notificacao iniciado.");
}

start().catch((error) => {
  logger.error(`Falha no MS Notificacao: ${error.message}`);
  process.exit(1);
});
