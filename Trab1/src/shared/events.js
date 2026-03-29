const { randomUUID } = require("crypto");

function stableStringify(value) {
  if (Array.isArray(value)) {
    return `[${value.map(stableStringify).join(",")}]`;
  }

  if (value && typeof value === "object") {
    const keys = Object.keys(value).sort();
    const props = keys.map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`);
    return `{${props.join(",")}}`;
  }

  return JSON.stringify(value);
}

function createEventEnvelope(eventType, producer, payload) {
  return {
    eventId: randomUUID(),
    eventType,
    producer,
    timestamp: new Date().toISOString(),
    payload,
    signature: null
  };
}

function signatureBase(event) {
  return stableStringify({
    eventId: event.eventId,
    eventType: event.eventType,
    producer: event.producer,
    timestamp: event.timestamp,
    payload: event.payload
  });
}

module.exports = {
  createEventEnvelope,
  signatureBase
};
