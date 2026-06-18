package com.promocoes.notificacao.config;

import com.promocoes.shared.messaging.Exchanges;
import com.promocoes.shared.messaging.Queues;
import com.promocoes.shared.messaging.RoutingKeys;
import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitConfig {

    @Bean
    public Queue notificacaoQueue() {
        return QueueBuilder.durable(Queues.NOTIFICACAO).build();
    }

    @Bean
    public Binding notificacaoPublicadaBinding(Queue notificacaoQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(notificacaoQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_PUBLICADA);
    }

    @Bean
    public Binding notificacaoDestaqueBinding(Queue notificacaoQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(notificacaoQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_DESTAQUE);
    }
}
