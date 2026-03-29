const fs = require("fs");
const path = require("path");
const { generateKeyPairSync } = require("crypto");

const services = ["gateway", "promocao", "ranking"];
const keysDir = path.resolve(__dirname, "../keys");

if (!fs.existsSync(keysDir)) {
  fs.mkdirSync(keysDir, { recursive: true });
}

for (const service of services) {
  const privatePath = path.join(keysDir, `${service}.private.pem`);
  const publicPath = path.join(keysDir, `${service}.public.pem`);

  const alreadyExists = fs.existsSync(privatePath) && fs.existsSync(publicPath);
  if (alreadyExists) {
    console.log(`Chaves de ${service} ja existem. Pulando.`);
    continue;
  }

  const { publicKey, privateKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: {
      type: "spki",
      format: "pem"
    },
    privateKeyEncoding: {
      type: "pkcs8",
      format: "pem"
    }
  });

  fs.writeFileSync(privatePath, privateKey, "utf8");
  fs.writeFileSync(publicPath, publicKey, "utf8");
  console.log(`Chaves de ${service} criadas.`);
}
