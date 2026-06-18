package com.promocoes.gateway.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class Notificacao {

    private long seq;
    private String type;
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
