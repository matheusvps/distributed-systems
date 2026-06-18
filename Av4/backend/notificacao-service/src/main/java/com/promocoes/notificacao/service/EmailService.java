package com.promocoes.notificacao.service;

import com.resend.Resend;
import com.resend.core.exception.ResendException;
import com.resend.services.emails.model.CreateEmailOptions;
import com.resend.services.emails.model.CreateEmailResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

@Slf4j
@Service
public class EmailService {

    @Value("${promocoes.email.provider:resend}")
    private String provider;

    @Value("${promocoes.email.api-key:}")
    private String apiKey;

    @Value("${promocoes.email.from:MS Notificacao <onboarding@resend.dev>}")
    private String from;

    public void send(String to, String subject, String text, String html) {
        if (!"resend".equalsIgnoreCase(provider) || apiKey == null || apiKey.isBlank()) {
            log.info("[EMAIL MOCK] to={} subject={} body={}", to, subject, text);
            return;
        }

        try {
            String safeHtml = html != null ? html : text;
            String safeText = text != null ? text : "";
            String safeFrom = from != null ? from : "MS Notificacao <onboarding@resend.dev>";

            Resend resend = new Resend(apiKey);

            CreateEmailOptions params = CreateEmailOptions.builder()
                    .from(safeFrom)
                    .to(to)
                    .subject(subject)
                    .html(safeHtml)
                    .text(safeText)
                    .build();

            CreateEmailResponse response = resend.emails().send(params);
            log.info("[EMAIL] Enviado com sucesso para {} | subject={} | id={}", to, subject, response.getId());
        } catch (ResendException e) {
            log.warn("[EMAIL] Falha ao enviar para {} | subject={} | erro={}", to, subject, e.getMessage());
        } catch (Exception e) {
            log.warn("[EMAIL] Erro inesperado ao enviar e-mail para {} | subject={} | erro={}", to, subject, e.getMessage());
        }
    }
}
