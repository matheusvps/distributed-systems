package com.promocoes.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class InteresseRequest {

    @NotBlank
    private String consumerId;

    @NotBlank
    private String category;
}
