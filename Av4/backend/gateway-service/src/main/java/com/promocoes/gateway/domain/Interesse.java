package com.promocoes.gateway.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Interesse de um consumidor por uma categoria. O par (consumerId, category) e unico.
 */
@Entity
@Table(name = "interesses", uniqueConstraints = @UniqueConstraint(columnNames = {"consumerId", "category"}))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Interesse {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String consumerId;
    private String category;
}
