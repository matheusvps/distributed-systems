package com.promocoes.notificacao.service;

import com.promocoes.notificacao.domain.Notificacao;
import com.promocoes.notificacao.dto.NotificacaoPayload;
import com.promocoes.notificacao.dto.PromocaoDestaquePayload;
import com.promocoes.notificacao.dto.PromocaoPublicadaPayload;
import com.promocoes.notificacao.repository.NotificacaoRepository;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.DomainEventPublisher;
import com.promocoes.shared.messaging.Exchanges;
import com.promocoes.shared.messaging.RoutingKeys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;

@Slf4j
@Service
@RequiredArgsConstructor
public class NotificacaoService {

    private static final String SOURCE = "notificacao";

    private final NotificacaoRepository repository;
    private final EmailService emailService;
    private final DomainEventPublisher publisher;

    public void onPromocaoPublicada(PromocaoPublicadaPayload payload) {
        String subject = "Sua promocao \"" + payload.getTitle() + "\" foi aprovada!";
        String body = "Parabens! Sua promocao \"" + payload.getTitle() + "\" na loja " + payload.getStore()
                + " foi aprovada e ja esta disponivel para os usuarios. "
                + "Categoria: " + payload.getCategory() + " | Preco: R$ " + payload.getPrice();
        emailService.send(payload.getStoreEmail(), subject, body, "<p>" + body + "</p>");

        NotificacaoPayload notifPayload = NotificacaoPayload.builder()
                .type("categoria")
                .message("Nova promocao publicada")
                .promotionId(payload.getId())
                .title(payload.getTitle())
                .category(payload.getCategory())
                .price(payload.getPrice())
                .store(payload.getStore())
                .build();

        publisher.publish(
                Exchanges.NOTIFICATIONS,
                RoutingKeys.categoria(payload.getCategory()),
                EventType.PROMOCAO_CATEGORIA,
                SOURCE,
                notifPayload
        );

        Notificacao log = Notificacao.builder()
                .type("categoria")
                .title(payload.getTitle())
                .message("Nova promocao publicada")
                .promotionId(payload.getId())
                .category(payload.getCategory())
                .createdAt(Instant.now())
                .build();
        repository.save(log);

        this.log.info("Notificacao categoria salva para promocao {}", payload.getId());
    }

    public void onPromocaoDestaque(PromocaoDestaquePayload payload) {
        String subject = "🔥 Sua promocao \"" + payload.getTitle() + "\" virou HOT DEAL!";
        String body = "Incrivel! Sua promocao \"" + payload.getTitle() + "\" na loja " + payload.getStore()
                + " atingiu destaque com score " + payload.getScore()
                + ". Votos positivos: " + payload.getPositiveVotes()
                + ". Categoria: " + payload.getCategory();
        emailService.send(payload.getStoreEmail(), subject, body, "<p>" + body + "</p>");

        NotificacaoPayload notifPayload = NotificacaoPayload.builder()
                .type("hotdeal")
                .message("Promocao em destaque (hot deal)")
                .promotionId(payload.getPromotionId())
                .title(payload.getTitle())
                .category(payload.getCategory())
                .score(payload.getScore())
                .store(payload.getStore())
                .tag("hot deal")
                .build();

        publisher.publish(
                Exchanges.NOTIFICATIONS,
                RoutingKeys.categoria(payload.getCategory()),
                EventType.PROMOCAO_CATEGORIA,
                SOURCE,
                notifPayload
        );

        Notificacao log = Notificacao.builder()
                .type("hotdeal")
                .title(payload.getTitle())
                .message("Promocao em destaque (hot deal)")
                .promotionId(payload.getPromotionId())
                .category(payload.getCategory())
                .createdAt(Instant.now())
                .build();
        repository.save(log);

        this.log.info("Notificacao hot deal salva para promocao {}", payload.getPromotionId());
    }
}
