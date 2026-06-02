package com.promocoes.promocao.repository;

import com.promocoes.promocao.domain.Promocao;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PromocaoRepository extends JpaRepository<Promocao, String> {
}
