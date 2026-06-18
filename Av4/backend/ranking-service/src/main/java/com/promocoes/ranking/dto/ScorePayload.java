package com.promocoes.ranking.dto;

import lombok.Builder;
import lombok.Data;

import java.time.Instant;

@Data
@Builder
public class ScorePayload {

    private String promotionId;
    private int score;
    private int positiveVotes;
    private int negativeVotes;
    private Instant updatedAt;
}
