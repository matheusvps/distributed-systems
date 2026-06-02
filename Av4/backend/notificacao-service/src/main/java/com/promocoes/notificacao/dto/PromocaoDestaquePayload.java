package com.promocoes.notificacao.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Payload do evento promocao.destaque (produzido pelo MS Ranking).
 */
@Data
public class PromocaoDestaquePayload {

    private String promotionId;
    private Double score;
    private Integer positiveVotes;
    private Integer negativeVotes;
    private String category;
    private String title;
    private String store;
    private String storeEmail;
    private BigDecimal price;
    private String tag;
    private Instant highlightedAt;
}
