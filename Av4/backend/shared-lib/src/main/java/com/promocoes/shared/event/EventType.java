package com.promocoes.shared.event;

/**
 * Tipos de evento (campo {@code type} do envelope). Espelham as routing keys de dominio.
 */
public final class EventType {

    public static final String PROMOCAO_RECEBIDA = "promocao.recebida";
    public static final String PROMOCAO_PUBLICADA = "promocao.publicada";
    public static final String PROMOCAO_VOTO = "promocao.voto";
    public static final String PROMOCAO_DESTAQUE = "promocao.destaque";
    public static final String PROMOCAO_CATEGORIA = "promocao.categoria";

    private EventType() {
    }
}
