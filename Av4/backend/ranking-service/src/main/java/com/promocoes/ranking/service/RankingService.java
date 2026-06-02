package com.promocoes.ranking.service;

import com.promocoes.ranking.domain.Score;
import com.promocoes.ranking.dto.DestaquePayload;
import com.promocoes.ranking.dto.VotoPayload;
import com.promocoes.ranking.repository.ScoreRepository;
import com.promocoes.shared.event.EventType;
import com.promocoes.shared.messaging.DomainEventPublisher;
import com.promocoes.shared.messaging.Exchanges;
import com.promocoes.shared.messaging.RoutingKeys;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;

/**
 * Regra de negocio do MS Ranking: acumula votos por promocao e publica destaque
 * quando o score atinge o threshold configurado.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RankingService {

    private static final String SOURCE = "ranking";

    private final ScoreRepository scoreRepository;
    private final DomainEventPublisher publisher;

    @Value("${promocoes.hot-deal-threshold:5}")
    private int hotDealThreshold;

    @Transactional
    public void processVoto(VotoPayload voto) {
        if (voto.getVote() != 1 && voto.getVote() != -1) {
            log.warn("Voto invalido recebido para promocao {}: vote={}", voto.getPromotionId(), voto.getVote());
            return;
        }

        Score score = scoreRepository.findById(voto.getPromotionId())
                .orElseGet(() -> Score.builder()
                        .promotionId(voto.getPromotionId())
                        .positiveVotes(0)
                        .negativeVotes(0)
                        .score(0)
                        .hotPublished(false)
                        .build());

        if (voto.getVote() == 1) {
            score.setPositiveVotes(score.getPositiveVotes() + 1);
        } else {
            score.setNegativeVotes(score.getNegativeVotes() + 1);
        }
        score.setScore(score.getPositiveVotes() - score.getNegativeVotes());

        scoreRepository.save(score);
        log.info("Voto processado para promocao {}: score={}, +{}/-{}",
                score.getPromotionId(), score.getScore(),
                score.getPositiveVotes(), score.getNegativeVotes());

        if (score.getScore() >= hotDealThreshold && !score.isHotPublished()) {
            score.setHotPublished(true);
            scoreRepository.save(score);

            DestaquePayload destaque = buildDestaquePayload(voto, score);
            publisher.publish(
                    Exchanges.EVENTS,
                    RoutingKeys.PROMOCAO_DESTAQUE,
                    EventType.PROMOCAO_DESTAQUE,
                    SOURCE,
                    destaque
            );
            log.info("HOT DEAL: promocao {} atingiu threshold {} (score={}).",
                    score.getPromotionId(), hotDealThreshold, score.getScore());
        }
    }

    private DestaquePayload buildDestaquePayload(VotoPayload voto, Score score) {
        String category = null;
        String title = null;
        String store = null;
        String storeEmail = null;
        java.math.BigDecimal price = null;

        if (voto.getPromotion() != null) {
            category = voto.getPromotion().getCategory();
            title = voto.getPromotion().getTitle();
            store = voto.getPromotion().getStore();
            storeEmail = voto.getPromotion().getStoreEmail();
            price = voto.getPromotion().getPrice();
        }

        return DestaquePayload.builder()
                .promotionId(score.getPromotionId())
                .score(score.getScore())
                .positiveVotes(score.getPositiveVotes())
                .negativeVotes(score.getNegativeVotes())
                .category(category)
                .title(title)
                .store(store)
                .storeEmail(storeEmail)
                .price(price)
                .tag("hot deal")
                .highlightedAt(Instant.now())
                .build();
    }
}
