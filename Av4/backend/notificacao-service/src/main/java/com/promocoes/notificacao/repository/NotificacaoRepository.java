package com.promocoes.notificacao.repository;

import com.promocoes.notificacao.domain.Notificacao;
import org.springframework.data.jpa.repository.JpaRepository;

public interface NotificacaoRepository extends JpaRepository<Notificacao, Long> {
}
