package com.promocoes.gateway.service;

import com.promocoes.gateway.domain.CatalogPromocao;
import com.promocoes.gateway.dto.CreatePromocaoRequest;
import com.promocoes.gateway.dto.VotoRequest;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.DomainEventPublisher;
import com.promocoes.shared.messaging.Exchanges;
import com.promocoes.shared.messaging.RoutingKeys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class PromocaoGatewayService {

    private static final String SOURCE = "gateway";

    private final DomainEventPublisher publisher;

    public PublishResult submitPromocao(CreatePromocaoRequest req) {
        String id = UUID.randomUUID().toString();

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("id", id);
        payload.put("title", req.getTitle());
        payload.put("description", req.getDescription());
        payload.put("category", req.getCategory());
        payload.put("price", req.getPrice());
        payload.put("originalPrice", req.getOriginalPrice());
        payload.put("store", req.getStore());
        payload.put("storeEmail", req.getStoreEmail());
        payload.put("createdAt", Instant.now());

        EventEnvelope event = publisher.publish(
                Exchanges.EVENTS,
                RoutingKeys.PROMOCAO_RECEBIDA,
                EventType.PROMOCAO_RECEBIDA,
                SOURCE,
                payload);

        return new PublishResult(id, event.getEventId());
    }

    public PublishResult submitVoto(CatalogPromocao promocao, VotoRequest req) {
        Map<String, Object> promo = new LinkedHashMap<>();
        promo.put("id", promocao.getId());
        promo.put("title", promocao.getTitle());
        promo.put("category", promocao.getCategory());
        promo.put("store", promocao.getStore());
        promo.put("storeEmail", promocao.getStoreEmail());
        promo.put("price", promocao.getPrice());

        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("promotionId", promocao.getId());
        payload.put("vote", req.getVote());
        payload.put("consumerId", req.getConsumerId());
        payload.put("votedAt", Instant.now());
        payload.put("promotion", promo);

        EventEnvelope event = publisher.publish(
                Exchanges.EVENTS,
                RoutingKeys.PROMOCAO_VOTO,
                EventType.PROMOCAO_VOTO,
                SOURCE,
                payload);

        return new PublishResult(promocao.getId(), event.getEventId());
    }

    public record PublishResult(String promotionId, String eventId) {
    }
}
