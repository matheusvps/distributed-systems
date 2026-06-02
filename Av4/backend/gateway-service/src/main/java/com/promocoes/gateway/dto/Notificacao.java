package com.promocoes.gateway.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

/**
 * Notificacao entregue ao frontend via SSE (evento "notificacao") e pela rota de polling.
 * Espelha o payload "flat" publicado pelo MS Notificacao (promocao.categoria), acrescido
 * de {@code seq} (ordem por consumidor) e {@code at} (recebimento no Gateway).
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Notificacao {

    private long seq;
    private String type;        // "categoria" | "hotdeal"
    private String message;
    private String promotionId;
    private String title;
    private String category;
    private Object price;
    private Object score;
    private String store;
    private String tag;
    private Instant at;
}
