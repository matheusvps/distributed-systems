package com.promocoes.shared.event;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Serializacao canonica (deterministica) usada como base da assinatura.
 *
 * Inclui todos os campos do envelope EXCETO {@code signature}. A canonicalizacao e feita
 * sobre uma arvore {@link JsonNode} normalizada para ser ROBUSTA ao round-trip
 * POJO -> wire -> Map dos consumidores:
 * <ul>
 *   <li>chaves de objeto ordenadas alfabeticamente (recursivo);</li>
 *   <li>numeros normalizados via {@link BigDecimal#stripTrailingZeros()} +
 *       {@code toPlainString()} (assim {@code 1499.90} == {@code 1499.9}, e {@code Double}
 *       vs {@code BigDecimal} produzem o mesmo texto);</li>
 *   <li>strings escapadas de forma consistente (datas ISO viram texto identico nos dois lados).</li>
 * </ul>
 * Garante que quem assina (com POJOs tipados) e quem verifica (com o payload como Map)
 * produzam exatamente os mesmos bytes.
 */
public final class CanonicalJson {

    private static final ObjectMapper MAPPER = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    public static byte[] bytes(EventEnvelope event) {
        Map<String, Object> base = new LinkedHashMap<>();
        base.put("eventId", event.getEventId());
        base.put("type", event.getType());
        base.put("timestamp", event.getTimestamp());
        base.put("source", event.getSource());
        base.put("payload", event.getPayload());

        JsonNode tree = MAPPER.valueToTree(base);
        StringBuilder sb = new StringBuilder();
        write(tree, sb);
        return sb.toString().getBytes(StandardCharsets.UTF_8);
    }

    private static void write(JsonNode node, StringBuilder sb) {
        if (node == null || node.isNull() || node.isMissingNode()) {
            sb.append("null");
        } else if (node.isObject()) {
            sb.append('{');
            List<String> names = new ArrayList<>();
            for (Iterator<String> it = node.fieldNames(); it.hasNext(); ) {
                names.add(it.next());
            }
            Collections.sort(names);
            for (int i = 0; i < names.size(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                writeString(names.get(i), sb);
                sb.append(':');
                write(node.get(names.get(i)), sb);
            }
            sb.append('}');
        } else if (node.isArray()) {
            sb.append('[');
            for (int i = 0; i < node.size(); i++) {
                if (i > 0) {
                    sb.append(',');
                }
                write(node.get(i), sb);
            }
            sb.append(']');
        } else if (node.isNumber()) {
            sb.append(new BigDecimal(node.asText()).stripTrailingZeros().toPlainString());
        } else if (node.isBoolean()) {
            sb.append(node.booleanValue() ? "true" : "false");
        } else {
            writeString(node.asText(), sb);
        }
    }

    private static void writeString(String value, StringBuilder sb) {
        try {
            // Reaproveita o escaping JSON do Jackson (aspas incluidas).
            sb.append(MAPPER.writeValueAsString(value));
        } catch (JsonProcessingException e) {
            throw new IllegalStateException("Falha ao escapar string canonica", e);
        }
    }

    private CanonicalJson() {
    }
}
