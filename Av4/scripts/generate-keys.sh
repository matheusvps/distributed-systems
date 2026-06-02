#!/usr/bin/env bash
# Gera pares RSA-2048 (PKCS#8 privada + SPKI/X.509 publica) para os 4 microsservicos.
# Todas as chaves ficam no mesmo diretorio keys/ (volume compartilhado): cada servico
# usa sua privada para assinar e qualquer publica para verificar.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/keys"
mkdir -p "$DIR"

for svc in gateway promocao ranking notificacao; do
  priv="$DIR/$svc.private.pem"
  pub="$DIR/$svc.public.pem"
  if [[ -f "$priv" && -f "$pub" ]]; then
    echo "Chaves de $svc ja existem. Pulando."
    continue
  fi
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -out "$priv" 2>/dev/null
  openssl pkey -in "$priv" -pubout -out "$pub" 2>/dev/null
  chmod 600 "$priv"
  echo "Chaves de $svc geradas."
done

echo "Chaves disponiveis em: $DIR"
ls -1 "$DIR"
