package com.promocoes.gateway.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class VotoRequest {

    @NotNull
    private Integer vote;

    @NotBlank
    private String consumerId;
}
