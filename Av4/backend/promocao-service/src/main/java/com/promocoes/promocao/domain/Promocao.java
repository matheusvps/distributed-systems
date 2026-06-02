package com.promocoes.promocao.domain;

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
 * Promocao validada e persistida pelo MS Promocao.
 */
@Entity
@Table(name = "promocoes")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Promocao {

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
    private Instant createdAt;
    private Instant validatedAt;
}
