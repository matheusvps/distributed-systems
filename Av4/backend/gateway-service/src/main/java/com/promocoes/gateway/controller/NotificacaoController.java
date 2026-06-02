package com.promocoes.gateway.controller;

import com.promocoes.gateway.dto.Notificacao;
import com.promocoes.gateway.service.SseHub;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.List;

@RestController
@RequestMapping("/api/notificacoes")
@RequiredArgsConstructor
public class NotificacaoController {

    private final SseHub sseHub;

    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream(@RequestParam String consumerId) {
        return sseHub.connect(consumerId);
    }

    @GetMapping
    public List<Notificacao> poll(@RequestParam String consumerId,
                                  @RequestParam(required = false, defaultValue = "0") long since) {
        return sseHub.buffered(consumerId, since);
    }
}
