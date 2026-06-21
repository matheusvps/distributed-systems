#!/usr/bin/env bash
# Gera pares RSA-2048 (PKCS#8 privada + SPKI/X.509 publica) para os 4 microsservicos.
# As chaves privadas ficam em keys/private/ por servico; as publicas em keys/public/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRIVATE_DIR="$ROOT/keys/private"
PUBLIC_DIR="$ROOT/keys/public"
mkdir -p "$PRIVATE_DIR" "$PUBLIC_DIR"

for svc in gateway promocao ranking notificacao; do
  priv="$PRIVATE_DIR/$svc.private.pem"
  pub="$PUBLIC_DIR/$svc.public.pem"
  if [[ -f "$priv" && -f "$pub" ]]; then
    echo "Chaves de $svc ja existem. Pulando."
    continue
  fi
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$priv" 2>/dev/null
  openssl pkey -in "$priv" -pubout -out "$pub" 2>/dev/null
  chmod 600 "$priv"
  echo "Chaves de $svc geradas."
done

echo "Chaves privadas disponiveis em: $PRIVATE_DIR"
ls -1 "$PRIVATE_DIR"
echo "Chaves publicas disponiveis em: $PUBLIC_DIR"
ls -1 "$PUBLIC_DIR"
