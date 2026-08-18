#!/usr/bin/env bash
# Download the IndicConformer Hindi STT model (AI4Bharat Pratinidhi successor)
# into ./models/.  Run once before first boot; the compose mounts ./models into
# the container so a pre-fetched copy is reused.
#
# The Pratinidhi checkpoint link in the AI4Bharat README is dead (403); the
# maintained equivalent is IndicConformer Hindi (hybrid CTC-RNNT, Conformer-L
# 120M) hosted on the AI4Bharat object store.  Runs on the AI4Bharat NeMo fork
# (nemo_toolkit 1.23.0rc0), NOT the PyPI 2.x package.
set -euo pipefail

MODELS_DIR="$(cd "$(dirname "$0")/.." && pwd)/models"
mkdir -p "$MODELS_DIR"

URL="https://objectstore.e2enetworks.net/indicconformer/models/indicconformer_stt_hi_hybrid_rnnt_large.nemo"
OUT="$MODELS_DIR/indicconformer_stt_hi_hybrid_rnnt_large.nemo"

if [[ -f "$OUT" ]]; then
    echo "$(basename "$OUT") present"
else
    echo "downloading $(basename "$OUT") (~523MB) ..."
    curl -L --fail --retry 3 -o "$OUT" "$URL"
fi

ls -la "$OUT"