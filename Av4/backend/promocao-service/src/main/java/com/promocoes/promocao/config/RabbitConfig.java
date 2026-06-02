package com.promocoes.promocao.config;

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

/**
 * Declara a fila do MS Promocao e a vincula a promocao.recebida no exchange de eventos.
 */
@Configuration
public class RabbitConfig {

    @Bean
    public Queue promocaoQueue() {
        return QueueBuilder.durable(Queues.PROMOCAO).build();
    }

    @Bean
    public Binding promocaoRecebidaBinding(Queue promocaoQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(promocaoQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_RECEBIDA);
    }
}
