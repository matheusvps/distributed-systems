package com.promocoes.gateway.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Payload dos eventos promocao.recebida / promocao.publicada / promocao.destaque
 * (espelha o contrato do MS Promocao).
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class PromocaoPayload {

    private String id;
    private String title;
    private String description;
    private String category;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String store;
    private String storeEmail;
    private Instant createdAt;
    private Instant validatedAt;
    private String status;
    private Integer score;
}
