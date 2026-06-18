package com.promocoes.promocao.service;

import com.promocoes.promocao.domain.Promocao;
import com.promocoes.promocao.dto.PromocaoPayload;
import com.promocoes.promocao.repository.PromocaoRepository;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.Validator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.Set;

@Slf4j
@Service
@RequiredArgsConstructor
public class PromocaoService {

    private final PromocaoRepository repository;
    private final Validator validator;

    public PromocaoPayload validateAndPersist(PromocaoPayload payload) {
        Set<ConstraintViolation<PromocaoPayload>> violations = validator.validate(payload);
        if (!violations.isEmpty()) {
            log.warn("Promocao invalida descartada: {}", violations);
            return null;
        }

        Instant now = Instant.now();
        Promocao entity = Promocao.builder()
                .id(payload.getId())
                .title(payload.getTitle())
                .description(payload.getDescription())
                .category(payload.getCategory())
                .price(payload.getPrice())
                .originalPrice(payload.getOriginalPrice())
                .store(payload.getStore())
                .storeEmail(payload.getStoreEmail())
                .status("publicada")
                .createdAt(payload.getCreatedAt() != null ? payload.getCreatedAt() : now)
                .validatedAt(now)
                .build();
        repository.save(entity);
        log.info("Promocao validada e persistida: {} - {}", entity.getId(), entity.getTitle());

        payload.setStatus("publicada");
        payload.setValidatedAt(now);
        return payload;
    }
}
