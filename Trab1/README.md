# Trab1 - Sistema de Promocoes com Microsservicos

Projeto da disciplina de Sistemas Distribuidos usando Node.js, RabbitMQ e eventos assinados digitalmente (RSA).

Alunos:
Matheus Vinicius Passos de Santana
Lucas Yukio Fukuda Matsumoto

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
- categorias disponiveis (`categories`)

Se quiser mudar categorias dos clientes ou limite de hot deal, edite esse arquivo.

## Como rodar

1. Garanta que o RabbitMQ esteja ativo em `amqp://localhost`.

### Opcao com Docker (RabbitMQ)

Se preferir, voce pode subir o RabbitMQ com Docker:

```bash
[ ! "$(docker ps -a -q -f name=rabbit-trab1)" ] && docker run -d --name rabbit-trab1 -p 5672:5672 -p 15672:15672 rabbitmq:3-management || docker start rabbit-trab1
```

<!-- ```powershell
if (-not ((docker ps -a -q -f name=rabbit-trab1 | Out-String).Trim())) { docker run -d --name rabbit-trab1 -p 5672:5672 -p 15672:15672 rabbitmq:3-management } else { docker start rabbit-trab1 }
``` -->

**Painel Administrativo (Web UI):**
- URL: [http://localhost:15672](http://localhost:15672)
- Usuário: `guest`
- Senha: `guest`

Para parar o container:

```bash
docker stop rabbit-trab1
```

Para deletar o container e os dados:

```bash
docker rm -f $(docker ps -a -q --filter ancestor=rabbitmq:3-management) 2>/dev/null || true
docker rmi rabbitmq:3-management
```

<!-- ```bash
$ids = docker ps -a -q --filter ancestor=rabbitmq:3-management; if ($ids) { docker rm -f $ids }; docker rmi rabbitmq:3-management 2>$null
```` -->

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
