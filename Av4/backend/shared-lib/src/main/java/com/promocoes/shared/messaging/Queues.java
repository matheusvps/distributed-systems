package com.promocoes.shared.messaging;

/**
 * Nomes das filas por microsservico. O Gateway possui duas filas:
 * uma para eventos de dominio (catalogo) e outra para notificacoes (SSE).
 */
public final class Queues {

    public static final String GATEWAY_EVENTS = "fila.gateway.events";
    public static final String GATEWAY_NOTIF = "fila.gateway.notif";
    public static final String PROMOCAO = "fila.promocao";
    public static final String RANKING = "fila.ranking";
    public static final String NOTIFICACAO = "fila.notificacao";

    private Queues() {
    }
}
