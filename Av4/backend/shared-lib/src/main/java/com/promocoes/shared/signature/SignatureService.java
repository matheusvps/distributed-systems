package com.promocoes.shared.signature;

import org.springframework.stereotype.Service;

import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Signature;
import java.util.Base64;

/**
 * Operacoes RSA de baixo nivel: assinatura/verificacao com SHA256withRSA, saida em Base64.
 * Equivalente ao crypto RSA-SHA256 do projeto Node original.
 */
@Service
public class SignatureService {

    private static final String ALGORITHM = "SHA256withRSA";

    public String sign(byte[] data, PrivateKey privateKey) {
        try {
            Signature signature = Signature.getInstance(ALGORITHM);
            signature.initSign(privateKey);
            signature.update(data);
            return Base64.getEncoder().encodeToString(signature.sign());
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao assinar: " + e.getMessage(), e);
        }
    }

    public boolean verify(byte[] data, String base64Signature, PublicKey publicKey) {
        if (base64Signature == null || base64Signature.isBlank()) {
            return false;
        }
        try {
            Signature signature = Signature.getInstance(ALGORITHM);
            signature.initVerify(publicKey);
            signature.update(data);
            return signature.verify(Base64.getDecoder().decode(base64Signature));
        } catch (Exception e) {
            return false;
        }
    }
}
