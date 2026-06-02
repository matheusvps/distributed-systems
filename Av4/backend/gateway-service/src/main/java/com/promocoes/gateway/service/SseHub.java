package com.promocoes.gateway.service;

import com.promocoes.gateway.dto.Notificacao;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Hub SSE em memoria: mantem os emitters abertos por consumidor e um ring buffer
 * por consumidor (ultimas ~100 notificacoes) para o fallback por polling.
 */
@Slf4j
@Service
public class SseHub {

    private static final int BUFFER_SIZE = 100;
    private static final long TIMEOUT = 0L; // sem timeout

    private final Map<String, List<SseEmitter>> emitters = new ConcurrentHashMap<>();
    private final Map<String, Deque<Notificacao>> buffers = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(0);

    /** Cria e registra um emitter para o consumidor. */
    public SseEmitter connect(String consumerId) {
        SseEmitter emitter = new SseEmitter(TIMEOUT);
        emitters.computeIfAbsent(consumerId, k -> new CopyOnWriteArrayList<>()).add(emitter);

        emitter.onCompletion(() -> remove(consumerId, emitter));
        emitter.onTimeout(() -> remove(consumerId, emitter));
        emitter.onError(e -> remove(consumerId, emitter));

        try {
            emitter.send(SseEmitter.event().name("ready").data("{\"status\":\"ready\"}"));
        } catch (IOException e) {
            remove(consumerId, emitter);
        }
        log.info("SSE conectado: consumerId={} (conexoes ativas={}).", consumerId, emitters.get(consumerId).size());
        return emitter;
    }

    private void remove(String consumerId, SseEmitter emitter) {
        List<SseEmitter> list = emitters.get(consumerId);
        if (list != null) {
            list.remove(emitter);
            if (list.isEmpty()) {
                emitters.remove(consumerId);
            }
        }
    }

    /** Entrega a notificacao a um consumidor: bufferiza e envia a todos os emitters dele. */
    public Notificacao deliver(String consumerId, Notificacao notificacao) {
        notificacao.setSeq(seq.incrementAndGet());

        Deque<Notificacao> buffer = buffers.computeIfAbsent(consumerId, k -> new ArrayDeque<>());
        synchronized (buffer) {
            buffer.addLast(notificacao);
            while (buffer.size() > BUFFER_SIZE) {
                buffer.removeFirst();
            }
        }

        List<SseEmitter> list = emitters.get(consumerId);
        if (list != null) {
            for (SseEmitter emitter : list) {
                try {
                    emitter.send(SseEmitter.event().name("notificacao").data(notificacao));
                } catch (Exception e) {
                    remove(consumerId, emitter);
                }
            }
        }
        return notificacao;
    }

    /** Notificacoes bufferizadas com seq > since. */
    public List<Notificacao> buffered(String consumerId, long since) {
        Deque<Notificacao> buffer = buffers.get(consumerId);
        List<Notificacao> result = new ArrayList<>();
        if (buffer != null) {
            synchronized (buffer) {
                for (Notificacao n : buffer) {
                    if (n.getSeq() > since) {
                        result.add(n);
                    }
                }
            }
        }
        return result;
    }

    /** Heartbeat para manter as conexoes vivas. */
    @Scheduled(fixedRate = 25000)
    public void heartbeat() {
        for (Map.Entry<String, List<SseEmitter>> entry : emitters.entrySet()) {
            for (SseEmitter emitter : entry.getValue()) {
                try {
                    emitter.send(SseEmitter.event().comment("heartbeat"));
                } catch (Exception e) {
                    remove(entry.getKey(), emitter);
                }
            }
        }
    }
}
