package com.promocoes.ranking.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Score de votos por promocao, persistido pelo MS Ranking.
 */
@Entity
@Table(name = "scores")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Score {

    @Id
    @Column(name = "promotion_id")
    private String promotionId;

    private int positiveVotes;
    private int negativeVotes;
    private int score;

    /** Indica se o evento promocao.destaque ja foi publicado para esta promocao (idempotencia). */
    private boolean hotPublished;
}
