package com.promocoes.notificacao.dto;

import lombok.Builder;
import lombok.Data;

import java.math.BigDecimal;

@Data
@Builder
public class NotificacaoPayload {

    private String type;
    private String message;
    private String promotionId;
    private String title;
    private String category;
    private BigDecimal price;
    private Double score;
    private String store;
    private String tag;
}
