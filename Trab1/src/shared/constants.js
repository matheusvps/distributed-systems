const EVENTS_EXCHANGE = "promocoes.events";
const NOTIFICATIONS_EXCHANGE = "promocoes.notificacoes";
const EXCHANGE_TYPE = "topic";

const ROUTING_KEYS = {
  PROMOCAO_RECEBIDA: "promocao.recebida",
  PROMOCAO_PUBLICADA: "promocao.publicada",
  PROMOCAO_VOTO: "promocao.voto",
  PROMOCAO_DESTAQUE: "promocao.destaque",
  PROMOCAO_CATEGORIA_PREFIX: "promocao.categoria"
};

const QUEUES = {
  GATEWAY: "fila.gateway",
  PROMOCAO: "fila.promocao",
  RANKING: "fila.ranking",
  NOTIFICACAO: "fila.notificacao"
};

module.exports = {
  EVENTS_EXCHANGE,
  NOTIFICATIONS_EXCHANGE,
  EXCHANGE_TYPE,
  ROUTING_KEYS,
  QUEUES
};
