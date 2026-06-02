package com.promocoes.shared.messaging;

/**
 * Nomes dos topic exchanges (reaproveitados do projeto Node original).
 * - EVENTS: eventos de dominio entre os microsservicos.
 * - NOTIFICATIONS: notificacoes destinadas ao Gateway (para SSE).
 */
public final class Exchanges {

    public static final String EVENTS = "promocoes.events";
    public static final String NOTIFICATIONS = "promocoes.notificacoes";

    private Exchanges() {
    }
}
