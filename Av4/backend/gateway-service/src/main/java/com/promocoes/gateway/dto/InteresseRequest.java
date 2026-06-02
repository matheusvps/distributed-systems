package com.promocoes.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * Corpo de POST/DELETE /api/interesses.
 */
@Data
public class InteresseRequest {

    @NotBlank
    private String consumerId;

    @NotBlank
    private String category;
}
