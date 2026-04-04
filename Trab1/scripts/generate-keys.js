const fs = require("fs");
const path = require("path");
const { generateKeyPairSync } = require("crypto");

const services = ["gateway", "promocao", "ranking"];
const baseDir = path.resolve(__dirname, "..");

const keyMap = {
  gateway: {
    private: ["src/gateway/keys/gateway.private.pem"],
    public: [
      "src/promocao/keys/gateway.public.pem",
      "src/ranking/keys/gateway.public.pem",
    ],
  },
  promocao: {
    private: ["src/promocao/keys/promocao.private.pem"],
    public: [
      "src/gateway/keys/promocao.public.pem",
      "src/notificacao/keys/promocao.public.pem",
    ],
  },
  ranking: {
    private: ["src/ranking/keys/ranking.private.pem"],
    public: ["src/notificacao/keys/ranking.public.pem"],
  },
};

function writeKey(filePath, content, isPrivate = false) {
  const fullPath = path.resolve(baseDir, filePath);
  const dir = path.dirname(fullPath);

  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }

  fs.writeFileSync(fullPath, content, "utf8");
  if (isPrivate) {
    fs.chmodSync(fullPath, 0o600);
  }
}

for (const service of services) {
  const config = keyMap[service];
  const allPaths = [...config.private, ...config.public];
  const existingKeys = allPaths.filter((p) => fs.existsSync(path.resolve(baseDir, p)));

  if (existingKeys.length > 0) {
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

  for (const privPath of config.private) {
    writeKey(privPath, privateKey, true);
  }

  for (const pubPath of config.public) {
    writeKey(pubPath, publicKey, false);
  }

  console.log(`Chaves de ${service} geradas.`);
}

console.log("Distribuicao de chaves concluida.");
