# Trab1 - Sistema de Promocoes com Microsservicos

Projeto da disciplina de Sistemas Distribuidos usando Node.js, RabbitMQ e eventos assinados digitalmente (RSA).

## Visao geral

O sistema tem 4 microsservicos e clientes consumidores:
- Gateway: interface no terminal para cadastrar promocao, listar e votar.
- Promocao: valida e publica promocoes recebidas.
- Ranking: processa votos e marca hot deal quando atinge o limite.
- Notificacao: distribui notificacoes por categoria e destaque.
- Cliente: consome notificacoes de categorias de interesse.

Comunicacao entre servicos acontece apenas por eventos no RabbitMQ (sem chamada direta entre microsservicos).

## Configuracao

Toda a configuracao fica no arquivo `config.js`:
- `rabbitmqUrl`
- `hotDealThreshold`
- perfis dos clientes (`clientProfiles`)

Se quiser mudar categorias dos clientes ou limite de hot deal, edite esse arquivo.

## Como rodar

1. Garanta que o RabbitMQ esteja ativo em `amqp://localhost`.

### Opcao com Docker (RabbitMQ)

Se preferir, voce pode subir o RabbitMQ com Docker:

```bash
docker run -d --name rabbit-trab1 -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

Painel web do RabbitMQ:
- URL: `http://localhost:15672`
- Usuario: `guest`
- Senha: `guest`

Para parar e remover o container:

```bash
docker stop rabbit-trab1
docker rm rabbit-trab1
```

2. Na pasta do projeto, execute:

```bash
npm install
npm run generate:keys
```

3. Abra 4 terminais e rode:

```bash
npm run start:promocao
npm run start:ranking
npm run start:notificacao
npm run start:gateway
```

4. Para simular clientes, abra novos terminais e rode:

```bash
npm run start:cliente:a
npm run start:cliente:b
```

5. No gateway:
- opcao 1: cadastra promocao
- opcao 2: lista promocoes validadas
- opcao 3: vota em promocao

Quando o score passar do limite configurado, o ranking publica `promocao.destaque` e os clientes inscritos recebem notificacao de hot deal.

## Estrutura rapida

- `src/shared`: utilitarios comuns (RabbitMQ, assinatura, logger)
- `src/gateway`, `src/promocao`, `src/ranking`, `src/notificacao`
- `src/cliente`
- `config.js`
