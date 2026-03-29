const fs = require("fs");
const path = require("path");
const { createSign, createVerify } = require("crypto");
const { signatureBase } = require("./events");

const keyCache = new Map();

function readKey(fileName) {
  const keyPath = path.resolve(__dirname, "../../keys", fileName);
  const cacheKey = keyPath;

  if (keyCache.has(cacheKey)) {
    return keyCache.get(cacheKey);
  }

  const key = fs.readFileSync(keyPath, "utf8");
  keyCache.set(cacheKey, key);
  return key;
}

function privateKeyFor(serviceName) {
  return readKey(`${serviceName}.private.pem`);
}

function publicKeyFor(serviceName) {
  return readKey(`${serviceName}.public.pem`);
}

function signEvent(event, serviceName) {
  const privateKey = privateKeyFor(serviceName);
  const signer = createSign("RSA-SHA256");
  signer.update(signatureBase(event));
  signer.end();
  return signer.sign(privateKey, "base64");
}

function verifyEvent(event) {
  if (!event || !event.signature || !event.producer) {
    return false;
  }

  try {
    const publicKey = publicKeyFor(event.producer);
    const verifier = createVerify("RSA-SHA256");
    verifier.update(signatureBase(event));
    verifier.end();
    return verifier.verify(publicKey, event.signature, "base64");
  } catch (error) {
    return false;
  }
}

module.exports = {
  signEvent,
  verifyEvent
};
