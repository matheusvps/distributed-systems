package com.promocoes.gateway.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.promocoes.gateway.dto.Notificacao;
import com.promocoes.gateway.service.InteresseService;
import com.promocoes.gateway.service.SseHub;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.signature.EventVerifier;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.List;
import java.util.Map;

/**
 * Consome promocao.categoria.# (exchange de notificacoes), descobre os consumidores
 * interessados na categoria e entrega a notificacao via SSE.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class NotificacaoConsumer {

    private final EventVerifier eventVerifier;
    private final InteresseService interesseService;
    private final SseHub sseHub;
    private final ObjectMapper objectMapper;

    @SuppressWarnings("unchecked")
    @RabbitListener(queues = Queues.GATEWAY_NOTIF)
    public void onNotificacao(EventEnvelope event) {
        if (!eventVerifier.isValid(event)) {
            return; // assinatura invalida ja logada
        }

        Map<String, Object> payload = objectMapper.convertValue(event.getPayload(), Map.class);
        String category = payload.get("category") != null ? String.valueOf(payload.get("category")) : null;
        String type = payload.get("type") != null ? String.valueOf(payload.get("type")) : "categoria";
        if (category == null) {
            log.warn("Notificacao ignorada: payload sem 'category'.");
            return;
        }

        // Repassa os campos "flat" publicados pelo MS Notificacao para o frontend.
        Notificacao notificacao = Notificacao.builder()
                .type(type)
                .category(category)
                .message(str(payload, "message"))
                .promotionId(str(payload, "promotionId"))
                .title(str(payload, "title"))
                .price(payload.get("price"))
                .score(payload.get("score"))
                .store(str(payload, "store"))
                .tag(str(payload, "tag"))
                .at(Instant.now())
                .build();

        List<String> interested = interesseService.consumersInterestedIn(category);
        for (String consumerId : interested) {
            sseHub.deliver(consumerId, notificacao);
        }
        log.info("Notificacao '{}' (categoria={}) entregue a {} consumidor(es).", type, category, interested.size());
    }

    private static String str(Map<String, Object> map, String key) {
        Object v = map.get(key);
        return v != null ? String.valueOf(v) : null;
    }
}
