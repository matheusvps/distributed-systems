package com.promocoes.gateway.domain;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Read model do catalogo de promocoes, alimentado pelos eventos
 * promocao.publicada (upsert) e promocao.destaque (hot/score).
 */
@Entity
@Table(name = "catalog_promocoes")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CatalogPromocao {

    @Id
    private String id;

    private String title;

    @Column(length = 1000)
    private String description;

    private String category;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String store;
    private String storeEmail;
    private String status;
    private Instant validatedAt;

    private boolean hot;
    private Integer score;
}
