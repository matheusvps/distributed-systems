package com.promocoes.notificacao.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/**
 * Servico de envio de e-mail via Resend HTTP API.
 * Se o provider nao for "resend" ou o api-key estiver em branco, apenas loga (modo mock).
 */
@Slf4j
@Service
public class EmailService {

    private static final String RESEND_API_URL = "https://api.resend.com/emails";

    @Value("${promocoes.email.provider:resend}")
    private String provider;

    @Value("${promocoes.email.api-key:}")
    private String apiKey;

    @Value("${promocoes.email.from:Promocoes <onboarding@resend.dev>}")
    private String from;

    private final HttpClient httpClient = HttpClient.newHttpClient();

    /**
     * Envia um e-mail. Nunca lanca excecao — erros sao capturados e logados.
     *
     * @param to      destinatario
     * @param subject assunto
     * @param text    corpo em texto puro
     * @param html    corpo em HTML
     */
    public void send(String to, String subject, String text, String html) {
        if (!"resend".equalsIgnoreCase(provider) || apiKey == null || apiKey.isBlank()) {
            log.info("[EMAIL MOCK] to={} subject={} body={}", to, subject, text);
            return;
        }

        try {
            String safeHtml = html != null ? html : text;
            String safeText = text != null ? text : "";
            String safeFrom = from != null ? from : "Promocoes <onboarding@resend.dev>";

            String jsonBody = String.format(
                    "{\"from\":\"%s\",\"to\":[\"%s\"],\"subject\":\"%s\",\"html\":\"%s\",\"text\":\"%s\"}",
                    escape(safeFrom),
                    escape(to),
                    escape(subject),
                    escape(safeHtml),
                    escape(safeText)
            );

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(RESEND_API_URL))
                    .header("Content-Type", "application/json")
                    .header("Authorization", "Bearer " + apiKey)
                    .POST(HttpRequest.BodyPublishers.ofString(jsonBody))
                    .build();

            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());

            if (response.statusCode() >= 200 && response.statusCode() < 300) {
                log.info("[EMAIL] Enviado com sucesso para {} | subject={} | response={}", to, subject, response.body());
            } else {
                log.warn("[EMAIL] Falha ao enviar para {} | status={} | response={}", to, response.statusCode(), response.body());
            }
        } catch (Exception e) {
            log.warn("[EMAIL] Erro ao enviar e-mail para {} | subject={} | erro={}", to, subject, e.getMessage());
        }
    }

    /** Escapa caracteres especiais JSON de forma simples. */
    private String escape(String value) {
        if (value == null) {
            return "";
        }
        return value
                .replace("\\", "\\\\")
                .replace("\"", "\\\"")
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t");
    }
}
