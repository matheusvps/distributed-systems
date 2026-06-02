package com.promocoes.ranking.dto;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Payload do evento promocao.destaque publicado quando uma promocao atinge o hot deal threshold.
 */
@Data
@Builder
public class DestaquePayload {

    private String promotionId;
    private int score;
    private int positiveVotes;
    private int negativeVotes;
    private String category;
    private String title;
    private String store;
    private String storeEmail;
    private BigDecimal price;
    private String tag;
    private Instant highlightedAt;
}
