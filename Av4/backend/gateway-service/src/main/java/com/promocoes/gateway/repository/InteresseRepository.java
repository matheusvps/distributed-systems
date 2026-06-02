package com.promocoes.gateway.repository;

import com.promocoes.gateway.domain.Interesse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.Optional;

public interface InteresseRepository extends JpaRepository<Interesse, Long> {

    List<Interesse> findByConsumerId(String consumerId);

    Optional<Interesse> findByConsumerIdAndCategory(String consumerId, String category);

    @Query("select i.consumerId from Interesse i where i.category = :category")
    List<String> findConsumerIdsByCategory(String category);

    @Query("select i.category from Interesse i where i.consumerId = :consumerId")
    List<String> findCategoriesByConsumerId(String consumerId);
}
