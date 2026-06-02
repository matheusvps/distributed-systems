package com.promocoes.gateway.controller;

import com.promocoes.gateway.domain.CatalogPromocao;
import com.promocoes.gateway.dto.CreatePromocaoRequest;
import com.promocoes.gateway.dto.VotoRequest;
import com.promocoes.gateway.service.CatalogService;
import com.promocoes.gateway.service.PromocaoGatewayService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/promocoes")
@RequiredArgsConstructor
public class PromocaoController {

    private final PromocaoGatewayService gatewayService;
    private final CatalogService catalogService;

    @PostMapping
    public ResponseEntity<Map<String, Object>> create(@Valid @RequestBody CreatePromocaoRequest req) {
        PromocaoGatewayService.PublishResult result = gatewayService.submitPromocao(req);
        return ResponseEntity.accepted().body(Map.of(
                "status", "accepted",
                "promotionId", result.promotionId(),
                "eventId", result.eventId()));
    }

    @GetMapping
    public Map<String, Object> list(@RequestParam(required = false) String category,
                                    @RequestParam(required = false) Boolean hot) {
        List<CatalogPromocao> promotions = catalogService.list(category, hot);
        return Map.of("count", promotions.size(), "promotions", promotions);
    }

    @PostMapping("/{id}/voto")
    public ResponseEntity<Map<String, Object>> voto(@PathVariable String id, @Valid @RequestBody VotoRequest req) {
        CatalogPromocao promocao = catalogService.findById(id)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Promocao nao encontrada: " + id));
        PromocaoGatewayService.PublishResult result = gatewayService.submitVoto(promocao, req);
        return ResponseEntity.accepted().body(Map.of(
                "status", "accepted",
                "promotionId", result.promotionId(),
                "eventId", result.eventId()));
    }
}
