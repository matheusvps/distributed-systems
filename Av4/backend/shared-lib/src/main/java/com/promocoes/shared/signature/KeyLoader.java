package com.promocoes.shared.signature;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.KeyFactory;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.concurrent.ConcurrentHashMap;

@Slf4j
@Component
public class KeyLoader {

    private final Path keysDir;
    private final ConcurrentHashMap<String, PrivateKey> privateCache = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, PublicKey> publicCache = new ConcurrentHashMap<>();

    public KeyLoader(@Value("${promocoes.keys-dir:keys}") String keysDir) {
        this.keysDir = Path.of(keysDir).toAbsolutePath().normalize();
        log.info("KeyLoader usando diretorio de chaves: {}", this.keysDir);
    }

    public PrivateKey privateKey(String service) {
        return privateCache.computeIfAbsent(service, this::readPrivate);
    }

    public PublicKey publicKey(String service) {
        return publicCache.computeIfAbsent(service, this::readPublic);
    }

    private PrivateKey readPrivate(String service) {
        try {
            byte[] der = readPem(service + ".private.pem");
            return KeyFactory.getInstance("RSA").generatePrivate(new PKCS8EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao carregar chave privada de '" + service + "': " + e.getMessage(), e);
        }
    }

    private PublicKey readPublic(String service) {
        try {
            byte[] der = readPem(service + ".public.pem");
            return KeyFactory.getInstance("RSA").generatePublic(new X509EncodedKeySpec(der));
        } catch (Exception e) {
            throw new IllegalStateException("Falha ao carregar chave publica de '" + service + "': " + e.getMessage(), e);
        }
    }

    private byte[] readPem(String fileName) throws Exception {
        Path path = keysDir.resolve(fileName);
        if (!Files.exists(path)) {
            throw new IllegalStateException("Chave nao encontrada: " + path + ". Gere as chaves (scripts/generate-keys.sh).");
        }
        String pem = Files.readString(path)
                .replaceAll("-----BEGIN (.*)-----", "")
                .replaceAll("-----END (.*)-----", "")
                .replaceAll("\\s", "");
        return Base64.getDecoder().decode(pem);
    }
}
