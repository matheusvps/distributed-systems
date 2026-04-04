module.exports = {
  rabbitmqUrl: process.env.RABBITMQ_URL || "amqp://localhost",
  hotDealThreshold: 5,
  defaultClientProfile: "clienteA",
  clientProfiles: {
    clienteA: {
      name: "Cliente_A",
      interests: ["livro", "jogo", "destaque"]
    },
    clienteB: {
      name: "Cliente_B",
      interests: ["jogo", "eletronico"]
    }
  },
  categories: ["livro", "jogo", "eletronico", "esporte", "alimento"]
};
