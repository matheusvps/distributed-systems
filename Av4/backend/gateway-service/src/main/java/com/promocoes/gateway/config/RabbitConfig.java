package com.promocoes.gateway.config;

import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.messaging.RoutingKeys;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Declara as filas do Gateway:
 * - fila.gateway.events: catalogo (promocao.publicada + promocao.destaque) no exchange de eventos.
 * - fila.gateway.notif: notificacoes por categoria (promocao.categoria.#) no exchange de notificacoes.
 *
 * Os TopicExchange (eventsExchange / notificationsExchange) vem da shared-lib RabbitMessagingConfig.
 */
@Configuration
public class RabbitConfig {

    @Bean
    public Queue gatewayEventsQueue() {
        return QueueBuilder.durable(Queues.GATEWAY_EVENTS).build();
    }

    @Bean
    public Binding gatewayPublicadaBinding(Queue gatewayEventsQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(gatewayEventsQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_PUBLICADA);
    }

    @Bean
    public Binding gatewayDestaqueBinding(Queue gatewayEventsQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(gatewayEventsQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_DESTAQUE);
    }

    @Bean
    public Queue gatewayNotifQueue() {
        return QueueBuilder.durable(Queues.GATEWAY_NOTIF).build();
    }

    @Bean
    public Binding gatewayNotifBinding(Queue gatewayNotifQueue, TopicExchange notificationsExchange) {
        return BindingBuilder.bind(gatewayNotifQueue).to(notificationsExchange).with(RoutingKeys.PROMOCAO_CATEGORIA_PATTERN);
    }
}
