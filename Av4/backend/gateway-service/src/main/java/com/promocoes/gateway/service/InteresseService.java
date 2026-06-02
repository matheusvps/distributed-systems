package com.promocoes.gateway.service;

import com.promocoes.gateway.domain.Interesse;
import com.promocoes.gateway.repository.InteresseRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Gerencia os interesses (consumerId x category) usados para filtrar as notificacoes.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class InteresseService {

    private final InteresseRepository repository;

    /** Registra o interesse (idempotente) e retorna as categorias atuais do consumidor. */
    public List<String> register(String consumerId, String category) {
        repository.findByConsumerIdAndCategory(consumerId, category)
                .orElseGet(() -> repository.save(
                        Interesse.builder().consumerId(consumerId).category(category).build()));
        log.info("Interesse registrado: consumerId={}, category={}.", consumerId, category);
        return repository.findCategoriesByConsumerId(consumerId);
    }

    /** Remove o interesse e retorna as categorias restantes do consumidor. */
    public List<String> remove(String consumerId, String category) {
        repository.findByConsumerIdAndCategory(consumerId, category)
                .ifPresent(repository::delete);
        log.info("Interesse removido: consumerId={}, category={}.", consumerId, category);
        return repository.findCategoriesByConsumerId(consumerId);
    }

    public List<String> categories(String consumerId) {
        return repository.findCategoriesByConsumerId(consumerId);
    }

    public List<String> consumersInterestedIn(String category) {
        return repository.findConsumerIdsByCategory(category);
    }
}
