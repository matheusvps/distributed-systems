package com.promocoes.shared.signature;

import com.promocoes.shared.event.CanonicalJson;
import com.promocoes.shared.event.EventEnvelope;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class EventVerifier {

    private final SignatureService signatureService;
    private final KeyLoader keyLoader;

    public boolean isValid(EventEnvelope event) {
        if (event == null || event.getSource() == null || event.getSignature() == null) {
            log.warn("Evento REJEITADO: envelope/assinatura/source ausente.");
            return false;
        }
        try {
            byte[] canonical = CanonicalJson.bytes(event);
            boolean ok = signatureService.verify(canonical, event.getSignature(), keyLoader.publicKey(event.getSource()));
            if (!ok) {
                log.warn("Evento {} REJEITADO: assinatura invalida (source={}).", event.getType(), event.getSource());
            }
            return ok;
        } catch (Exception e) {
            log.warn("Evento {} REJEITADO: erro ao verificar assinatura: {}", event.getType(), e.getMessage());
            return false;
        }
    }
}
