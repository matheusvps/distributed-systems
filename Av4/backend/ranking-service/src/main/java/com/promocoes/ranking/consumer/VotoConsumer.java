package com.promocoes.ranking.consumer;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.promocoes.ranking.dto.VotoPayload;
import com.promocoes.ranking.service.RankingService;
import com.promocoes.shared.event.EventEnvelope;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.signature.EventVerifier;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class VotoConsumer {

    private final EventVerifier eventVerifier;
    private final RankingService rankingService;
    private final ObjectMapper objectMapper;

    @RabbitListener(queues = Queues.RANKING)
    public void onVoto(EventEnvelope event) {
        if (!eventVerifier.isValid(event)) {
            return;
        }
        log.info("Evento {} aceito (assinatura OK, source={}).", event.getType(), event.getSource());

        VotoPayload voto = objectMapper.convertValue(event.getPayload(), VotoPayload.class);
        rankingService.processVoto(voto);
    }
}
