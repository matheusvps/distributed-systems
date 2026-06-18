package com.promocoes.notificacao.dto;

import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

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
