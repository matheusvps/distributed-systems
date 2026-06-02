package com.promocoes.gateway.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class MiscController {

    private static final List<String> CATEGORIES = List.of("livro", "jogo", "eletronico", "esporte", "alimento");

    @GetMapping("/categorias")
    public Map<String, Object> categorias() {
        return Map.of("categories", CATEGORIES);
    }

    @GetMapping("/health")
    public Map<String, Object> health() {
        return Map.of(
                "status", "ok",
                "service", "gateway",
                "time", Instant.now());
    }
}
