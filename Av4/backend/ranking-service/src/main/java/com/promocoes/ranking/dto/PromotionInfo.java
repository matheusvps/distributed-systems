package com.promocoes.ranking.dto;

import lombok.Data;

import java.math.BigDecimal;

/**
 * Sub-objeto promotion dentro do payload de promocao.voto.
 */
@Data
public class PromotionInfo {

    private String id;
    private String title;
    private String category;
    private String store;
    private String storeEmail;
    private BigDecimal price;
}
