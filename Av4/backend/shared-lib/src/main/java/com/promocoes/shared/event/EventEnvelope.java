package com.promocoes.shared.event;

import com.fasterxml.jackson.annotation.JsonInclude;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.Instant;
import java.util.UUID;

/**
 * Envelope padrao de TODOS os eventos (reaproveitado do projeto Node).
 *
 * <pre>
 * {
 *   "eventId": "uuid",
 *   "type": "promocao.recebida",
 *   "timestamp": "ISO_DATE",
 *   "source": "gateway",
 *   "signature": "base64",
 *   "payload": { ... }
 * }
 * </pre>
 *
 * A assinatura cobre todos os campos EXCETO {@code signature} (ver {@link CanonicalJson}).
 * O {@code payload} e um mapa generico para manter o contrato flexivel entre servicos.
 */
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

    /** Cria um envelope novo (sem assinatura) pronto para ser assinado. */
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
