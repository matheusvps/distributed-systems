package com.promocoes.gateway.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.math.BigDecimal;

/**
 * Corpo do POST /api/promocoes.
 */
@Data
public class CreatePromocaoRequest {

    @NotBlank
    private String title;

    private String description;

    @NotBlank
    private String category;

    @NotNull
    @Positive
    private BigDecimal price;

    private BigDecimal originalPrice;

    @NotBlank
    private String store;

    @NotBlank
    @Email
    private String storeEmail;
}
