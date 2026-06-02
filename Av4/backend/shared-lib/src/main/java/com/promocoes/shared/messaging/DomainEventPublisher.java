package com.promocoes.shared.messaging;

import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.signature.EventSigner;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

/**
 * Publica eventos de dominio: cria o envelope, ASSINA com a chave do produtor e envia
 * ao exchange/routing key. Usado por todos os microsservicos para garantir o mesmo
 * formato e a assinatura consistente.
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class DomainEventPublisher {

    private final RabbitTemplate rabbitTemplate;
    private final EventSigner eventSigner;

    public EventEnvelope publish(String exchange, String routingKey, String type, String source, Object payload) {
        EventEnvelope event = EventEnvelope.create(type, source, payload);
        eventSigner.sign(event);
        rabbitTemplate.convertAndSend(exchange, routingKey, event);
        log.info("Evento {} publicado e assinado por {} (rk={}, id={}).", type, source, routingKey, event.getEventId());
        return event;
    }
}
