package com.promocoes.ranking.dto;

import lombok.Data;

import java.time.Instant;

/**
 * Payload do evento promocao.voto.
 */
@Data
public class VotoPayload {

    private String promotionId;
    private int vote;
    private String consumerId;
    private Instant votedAt;
    private PromotionInfo promotion;
}
