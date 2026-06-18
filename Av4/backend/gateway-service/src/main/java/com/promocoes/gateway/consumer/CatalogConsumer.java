package com.promocoes.gateway.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.promocoes.gateway.dto.PromocaoPayload;
import com.promocoes.gateway.service.CatalogService;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.signature.EventVerifier;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

import java.util.Map;

@Slf4j
@Component
@RequiredArgsConstructor
public class CatalogConsumer {

    private final EventVerifier eventVerifier;
    private final CatalogService catalogService;
    private final ObjectMapper objectMapper;

    @RabbitListener(queues = Queues.GATEWAY_EVENTS)
    public void onEvent(EventEnvelope event) {
        if (!eventVerifier.isValid(event)) {
            return;
        }
        log.info("Evento {} aceito (assinatura OK, source={}).", event.getType(), event.getSource());

        if (EventType.PROMOCAO_PUBLICADA.equals(event.getType())) {
            PromocaoPayload payload = objectMapper.convertValue(event.getPayload(), PromocaoPayload.class);
            catalogService.upsert(payload);
        } else if (EventType.PROMOCAO_DESTAQUE.equals(event.getType())) {
            @SuppressWarnings("unchecked")
            Map<String, Object> p = objectMapper.convertValue(event.getPayload(), Map.class);
            String promotionId = p.get("promotionId") != null ? String.valueOf(p.get("promotionId")) : null;
            Integer score = p.get("score") != null ? ((Number) p.get("score")).intValue() : null;
            catalogService.markHot(promotionId, score);
        } else {
            log.warn("Evento ignorado no catalogo (tipo inesperado): {}", event.getType());
        }
    }
}
