package com.promocoes.shared.signature;

import com.promocoes.shared.event.CanonicalJson;
import com.promocoes.shared.event.EventEnvelope;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class EventSigner {

    private final SignatureService signatureService;
    private final KeyLoader keyLoader;

    public EventEnvelope sign(EventEnvelope event) {
        byte[] canonical = CanonicalJson.bytes(event);
        String signature = signatureService.sign(canonical, keyLoader.privateKey(event.getSource()));
        event.setSignature(signature);
        return event;
    }
}
