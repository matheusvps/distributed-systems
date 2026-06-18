package com.promocoes.shared.event;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@JsonInclude(JsonInclude.Include.NON_NULL)
public class EventEnvelope {

    private String eventId;
    private String type;
    private Instant timestamp;
    private String source;
    private String signature;
    private Object payload;

    public static EventEnvelope create(String type, String source, Object payload) {
        return EventEnvelope.builder()
                .eventId(UUID.randomUUID().toString())
                .type(type)
                .source(source)
                .timestamp(Instant.now())
                .payload(payload)
                .build();
    }
}
