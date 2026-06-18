package com.promocoes.promocao.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.promocoes.promocao.dto.PromocaoPayload;
import com.promocoes.promocao.service.PromocaoService;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.DomainEventPublisher;
import com.promocoes.shared.messaging.Exchanges;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.messaging.RoutingKeys;
import com.promocoes.shared.signature.EventVerifier;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class PromocaoConsumer {

    private static final String SOURCE = "promocao";

    private final EventVerifier eventVerifier;
    private final PromocaoService promocaoService;
    private final DomainEventPublisher publisher;
    private final ObjectMapper objectMapper;

    @RabbitListener(queues = Queues.PROMOCAO)
    public void onPromocaoRecebida(EventEnvelope event) {
        if (!eventVerifier.isValid(event)) {
            return;
        }
        log.info("Evento {} aceito (assinatura OK, source={}).", event.getType(), event.getSource());

        PromocaoPayload payload = objectMapper.convertValue(event.getPayload(), PromocaoPayload.class);
        PromocaoPayload publicada = promocaoService.validateAndPersist(payload);
        if (publicada == null) {
            return;
        }

        publisher.publish(
                Exchanges.EVENTS,
                RoutingKeys.PROMOCAO_PUBLICADA,
                EventType.PROMOCAO_PUBLICADA,
                SOURCE,
                publicada
        );
    }
}
