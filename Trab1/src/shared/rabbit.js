const amqp = require("amqplib");
const {
  EVENTS_EXCHANGE,
  NOTIFICATIONS_EXCHANGE,
  EXCHANGE_TYPE
} = require("./constants");
const config = require("../../config");

async function createRabbitChannel(logger) {
  const url = config.rabbitmqUrl;
  const connection = await amqp.connect(url);
  const channel = await connection.createChannel();

  await channel.assertExchange(EVENTS_EXCHANGE, EXCHANGE_TYPE, { durable: false });
  await channel.assertExchange(NOTIFICATIONS_EXCHANGE, EXCHANGE_TYPE, { durable: false });

  connection.on("error", (error) => {
    logger.error(`Erro de conexao RabbitMQ: ${error.message}`);
  });

  connection.on("close", () => {
    logger.warn("Conexao RabbitMQ encerrada.");
  });

  return { connection, channel };
}

async function subscribe({
  channel,
  queue,
  exchange,
  routingKeys,
  onMessage,
  logger
}) {
  await channel.assertQueue(queue, { durable: false });

  for (const key of routingKeys) {
    await channel.bindQueue(queue, exchange, key);
  }

  await channel.consume(queue, async (message) => {
    if (!message) {
      return;
    }

    try {
      const parsed = JSON.parse(message.content.toString("utf8"));
      await onMessage(parsed, message.fields.routingKey);
      channel.ack(message);
    } catch (error) {
      logger.error(`Erro ao processar mensagem: ${error.message}`);
      channel.ack(message);
    }
  });
}

function publish(channel, exchange, routingKey, payload) {
  channel.publish(exchange, routingKey, Buffer.from(JSON.stringify(payload), "utf8"), {
    contentType: "application/json"
  });
}

module.exports = {
  createRabbitChannel,
  subscribe,
  publish
};
