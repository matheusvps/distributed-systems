package com.promocoes.ranking.config;

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
    public Queue rankingQueue() {
        return QueueBuilder.durable(Queues.RANKING).build();
    }

    @Bean
    public Binding rankingVotoBinding(Queue rankingQueue, TopicExchange eventsExchange) {
        return BindingBuilder.bind(rankingQueue).to(eventsExchange).with(RoutingKeys.PROMOCAO_VOTO);
    }
}
