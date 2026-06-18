package com.promocoes.gateway.service;

import com.promocoes.gateway.domain.CatalogPromocao;
import com.promocoes.gateway.dto.PromocaoPayload;
import com.promocoes.gateway.repository.CatalogPromocaoRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class CatalogService {

    private final CatalogPromocaoRepository repository;

    public List<CatalogPromocao> list(String category, Boolean hot) {
        if (category != null && hot != null) {
            return repository.findByCategoryAndHot(category, hot);
        }
        if (category != null) {
            return repository.findByCategory(category);
        }
        if (hot != null) {
            return repository.findByHot(hot);
        }
        return repository.findAll();
    }

    public Optional<CatalogPromocao> findById(String id) {
        return repository.findById(id);
    }

    public void upsert(PromocaoPayload payload) {
        CatalogPromocao existing = repository.findById(payload.getId()).orElse(null);
        CatalogPromocao entity = CatalogPromocao.builder()
                .id(payload.getId())
                .title(payload.getTitle())
                .description(payload.getDescription())
                .category(payload.getCategory())
                .price(payload.getPrice())
                .originalPrice(payload.getOriginalPrice())
                .store(payload.getStore())
                .storeEmail(payload.getStoreEmail())
                .status(payload.getStatus() != null ? payload.getStatus() : "publicada")
                .validatedAt(payload.getValidatedAt())
                .hot(existing != null && existing.isHot())
                .score(existing != null && existing.getScore() != null ? existing.getScore() : 0)
                .build();
        repository.save(entity);
        log.info("Catalogo atualizado (upsert): {} - {}", entity.getId(), entity.getTitle());
    }

    public void updateScore(String id, Integer score) {
        if (id == null) {
            log.warn("Catalogo: score ignorado, promotionId ausente no evento.");
            return;
        }
        repository.findById(id).ifPresentOrElse(item -> {
            item.setScore(score);
            repository.save(item);
            log.info("Catalogo: score da promocao {} atualizado para {}.", id, score);
        }, () -> log.warn("Catalogo: score ignorado, promocao {} nao encontrada.", id));
    }

    public void markHot(String id, Integer score) {
        if (id == null) {
            log.warn("Catalogo: destaque ignorado, promotionId ausente no evento.");
            return;
        }
        repository.findById(id).ifPresentOrElse(item -> {
            item.setHot(true);
            item.setScore(score);
            repository.save(item);
            log.info("Catalogo: promocao {} marcada como destaque (score={}).", id, score);
        }, () -> log.warn("Catalogo: destaque ignorado, promocao {} nao encontrada.", id));
    }
}
