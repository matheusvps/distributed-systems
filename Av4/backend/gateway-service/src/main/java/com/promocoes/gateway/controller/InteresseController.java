package com.promocoes.gateway.controller;

import com.promocoes.gateway.dto.InteresseRequest;
import com.promocoes.gateway.service.InteresseService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/interesses")
@RequiredArgsConstructor
public class InteresseController {

    private final InteresseService interesseService;

    @PostMapping
    public Map<String, Object> register(@Valid @RequestBody InteresseRequest req) {
        return Map.of(
                "consumerId", req.getConsumerId(),
                "interests", interesseService.register(req.getConsumerId(), req.getCategory()));
    }

    @DeleteMapping
    public Map<String, Object> remove(@Valid @RequestBody InteresseRequest req) {
        return Map.of(
                "consumerId", req.getConsumerId(),
                "interests", interesseService.remove(req.getConsumerId(), req.getCategory()));
    }

    @GetMapping
    public Map<String, Object> list(@RequestParam String consumerId) {
        return Map.of(
                "consumerId", consumerId,
                "interests", interesseService.categories(consumerId));
    }
}
