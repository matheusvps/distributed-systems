package com.promocoes.ranking.repository;

import com.promocoes.ranking.domain.Score;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ScoreRepository extends JpaRepository<Score, String> {
}
