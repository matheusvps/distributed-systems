package com.promocoes.shared.messaging;

/**
 * Routing keys dos eventos (reaproveitadas do projeto Node original).
 * As notificacoes por categoria usam o prefixo {@code promocao.categoria.<categoria>}.
 */
public final class RoutingKeys {

    public static final String PROMOCAO_RECEBIDA = "promocao.recebida";
    public static final String PROMOCAO_PUBLICADA = "promocao.publicada";
    public static final String PROMOCAO_VOTO = "promocao.voto";
    public static final String PROMOCAO_DESTAQUE = "promocao.destaque";
    public static final String PROMOCAO_CATEGORIA_PREFIX = "promocao.categoria";
    /** Padrao para consumir todas as categorias. */
    public static final String PROMOCAO_CATEGORIA_PATTERN = "promocao.categoria.#";

    public static String categoria(String categoria) {
        return PROMOCAO_CATEGORIA_PREFIX + "." + (categoria == null ? "geral" : categoria.toLowerCase());
    }

    private RoutingKeys() {
    }
}
