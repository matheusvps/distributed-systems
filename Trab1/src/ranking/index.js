const { createEventEnvelope } = require("../shared/events");
const { signEvent, verifyEvent } = require("../shared/signature");
const { createLogger } = require("../shared/logger");
const { createRabbitChannel, publish, subscribe } = require("../shared/rabbit");
const config = require("../../config");
const {
  EVENTS_EXCHANGE,
  ROUTING_KEYS,
  QUEUES
} = require("../shared/constants");

const SERVICE_NAME = "ranking";
const logger = createLogger("MS Ranking");
const HOT_DEAL_THRESHOLD = Number(config.hotDealThreshold || 5);
const rankingState = new Map();

function calculateScore(state) {
  return state.positive - state.negative;
}

async function start() {
  const { channel } = await createRabbitChannel(logger);

  await subscribe({
    channel,
    queue: QUEUES.RANKING,
    exchange: EVENTS_EXCHANGE,
    routingKeys: [ROUTING_KEYS.PROMOCAO_VOTO],
    logger,
    onMessage: async (event) => {
      if (!verifyEvent(event)) {
        logger.warn("Evento promocao.voto descartado por assinatura invalida.");
        return;
      }

      const { promotionId, vote, promotion } = event.payload || {};

      if (!promotionId || ![1, -1].includes(vote)) {
        logger.warn("Evento de voto invalido descartado.");
        return;
      }

      const current = rankingState.get(promotionId) || {
        positive: 0,
        negative: 0,
        score: 0,
        hotDealPublished: false
      };

      if (vote === 1) {
        current.positive += 1;
      } else {
        current.negative += 1;
      }

      current.score = calculateScore(current);
      rankingState.set(promotionId, current);

      logger.info(
        `Voto processado para ${promotionId}. Score=${current.score} (+:${current.positive} -:${current.negative})`
      );

      if (current.score >= HOT_DEAL_THRESHOLD && !current.hotDealPublished) {
        current.hotDealPublished = true;

        const highlightEvent = createEventEnvelope(ROUTING_KEYS.PROMOCAO_DESTAQUE, SERVICE_NAME, {
          promotionId,
          score: current.score,
          positiveVotes: current.positive,
          negativeVotes: current.negative,
          category: promotion?.category || "geral",
          title: promotion?.title || "Promocao",
          tag: "hot deal",
          highlightedAt: new Date().toISOString()
        });

        highlightEvent.signature = signEvent(highlightEvent, SERVICE_NAME);

        publish(channel, EVENTS_EXCHANGE, ROUTING_KEYS.PROMOCAO_DESTAQUE, highlightEvent);
        logger.info(`Evento ${ROUTING_KEYS.PROMOCAO_DESTAQUE} publicado para ${promotionId}.`);
      }
    }
  });

  logger.info(`MS Ranking iniciado. Limite de hot deal: ${HOT_DEAL_THRESHOLD}.`);
}

start().catch((error) => {
  logger.error(`Falha no MS Ranking: ${error.message}`);
  process.exit(1);
});
