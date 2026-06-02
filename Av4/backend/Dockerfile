# Dockerfile parametrizado para qualquer um dos 4 microsservicos.
# Uso: docker build --build-arg SERVICE=gateway-service ...
# (o docker-compose ja passa o SERVICE de cada um).
FROM maven:3.9-eclipse-temurin-21 AS build
ARG SERVICE
WORKDIR /build
COPY . .
# -am compila o shared-lib (dependencia) junto; -pl restringe ao servico alvo.
RUN mvn -q -pl ${SERVICE} -am -DskipTests package

FROM eclipse-temurin:21-jre
ARG SERVICE
WORKDIR /app
COPY --from=build /build/${SERVICE}/target/${SERVICE}.jar app.jar
# Diretorio de chaves RSA montado como volume compartilhado.
ENV KEYS_DIR=/keys
ENTRYPOINT ["java", "-jar", "app.jar"]
