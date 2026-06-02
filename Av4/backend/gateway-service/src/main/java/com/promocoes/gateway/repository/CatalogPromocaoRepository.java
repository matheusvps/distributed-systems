package com.promocoes.gateway.repository;

import com.promocoes.gateway.domain.CatalogPromocao;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CatalogPromocaoRepository extends JpaRepository<CatalogPromocao, String> {

    List<CatalogPromocao> findByCategory(String category);

    List<CatalogPromocao> findByHot(boolean hot);

    List<CatalogPromocao> findByCategoryAndHot(String category, boolean hot);
}
