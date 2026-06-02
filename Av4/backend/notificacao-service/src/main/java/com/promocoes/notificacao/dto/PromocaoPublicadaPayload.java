package com.promocoes.notificacao.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Payload do evento promocao.publicada (produzido pelo MS Promocao).
 */
@Data
public class PromocaoPublicadaPayload {

    private String id;
    private String title;
    private String description;
    private String category;
    private BigDecimal price;
    private BigDecimal originalPrice;
    private String store;
    private String storeEmail;
    private String status;
    private Instant validatedAt;
}
