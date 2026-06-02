package com.promocoes.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * Corpo do POST /api/promocoes/{id}/voto. vote deve ser 1 ou -1.
 */
@Data
public class VotoRequest {

    @NotNull
    private Integer vote;

    @NotBlank
    private String consumerId;
}
