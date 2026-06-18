package com.promocoes.notificacao.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.promocoes.notificacao.dto.PromocaoDestaquePayload;
import com.promocoes.notificacao.dto.PromocaoPublicadaPayload;
import com.promocoes.notificacao.service.NotificacaoService;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.signature.EventVerifier;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class NotificacaoConsumer {

    private final EventVerifier eventVerifier;
    private final NotificacaoService notificacaoService;
    private final ObjectMapper objectMapper;

    @RabbitListener(queues = Queues.NOTIFICACAO)
    public void onEvent(EventEnvelope event) {
        if (!eventVerifier.isValid(event)) {
            return;
        }
        log.info("Evento {} aceito (assinatura OK, source={}).", event.getType(), event.getSource());

        if (EventType.PROMOCAO_PUBLICADA.equals(event.getType())) {
            PromocaoPublicadaPayload payload = objectMapper.convertValue(event.getPayload(), PromocaoPublicadaPayload.class);
            notificacaoService.onPromocaoPublicada(payload);
        } else if (EventType.PROMOCAO_DESTAQUE.equals(event.getType())) {
            PromocaoDestaquePayload payload = objectMapper.convertValue(event.getPayload(), PromocaoDestaquePayload.class);
            notificacaoService.onPromocaoDestaque(payload);
        } else {
            log.warn("Tipo de evento nao tratado: {}", event.getType());
        }
    }
}
