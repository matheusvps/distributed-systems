package com.promocoes.promocao.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import lombok.Data;

import java.math.BigDecimal;
import java.time.Instant;

/**
 * Payload do evento promocao.recebida / promocao.publicada.
 */
@Data
public class PromocaoPayload {

    @NotBlank
    private String id;

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

    private Instant createdAt;
    private Instant validatedAt;
    private String status;
}
