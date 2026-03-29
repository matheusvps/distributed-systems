const { createEventEnvelope } = require("../shared/events");
const { signEvent, verifyEvent } = require("../shared/signature");
const { createLogger } = require("../shared/logger");
const { createRabbitChannel, publish, subscribe } = require("../shared/rabbit");
const {
  EVENTS_EXCHANGE,
  ROUTING_KEYS,
  QUEUES
} = require("../shared/constants");

const SERVICE_NAME = "promocao";
const logger = createLogger("MS Promocao");
const promotions = new Map();

function isPromotionValid(promo) {
  return (
    promo &&
    typeof promo.id === "string" &&
    typeof promo.title === "string" &&
    typeof promo.category === "string" &&
    typeof promo.store === "string" &&
    Number.isFinite(promo.price) &&
    promo.price > 0
  );
}

async function start() {
  const { channel } = await createRabbitChannel(logger);

  await subscribe({
    channel,
    queue: QUEUES.PROMOCAO,
    exchange: EVENTS_EXCHANGE,
    routingKeys: [ROUTING_KEYS.PROMOCAO_RECEBIDA],
    logger,
    onMessage: async (event) => {
      if (!verifyEvent(event)) {
        logger.warn("Evento promocao.recebida descartado por assinatura invalida.");
        return;
      }

      const promo = event.payload;

      if (!isPromotionValid(promo)) {
        logger.warn(`Promocao invalida descartada: ${JSON.stringify(promo)}`);
        return;
      }

      promotions.set(promo.id, promo);
      logger.info(`Promocao validada: ${promo.id} - ${promo.title}`);

      const publishEvent = createEventEnvelope(ROUTING_KEYS.PROMOCAO_PUBLICADA, SERVICE_NAME, {
        ...promo,
        validatedAt: new Date().toISOString()
      });
      publishEvent.signature = signEvent(publishEvent, SERVICE_NAME);

      publish(channel, EVENTS_EXCHANGE, ROUTING_KEYS.PROMOCAO_PUBLICADA, publishEvent);
      logger.info(`Evento ${ROUTING_KEYS.PROMOCAO_PUBLICADA} publicado (${promo.id}).`);
    }
  });

  logger.info("MS Promocao iniciado.");
}

start().catch((error) => {
  logger.error(`Falha no MS Promocao: ${error.message}`);
  process.exit(1);
});
