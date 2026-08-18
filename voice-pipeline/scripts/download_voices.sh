#!/usr/bin/env bash
# Download the Piper voices used by the voice-pipeline /tts endpoint into
# ./models/.  Run once before first boot; the compose mounts ./models into the
# container so a pre-fetched copy is reused.
#
# Voices (rhasspy/piper-voices, v1.0.0 tag):
#   hi_IN-pratham-medium  — Hindi (male), the demo voice
#   en_US-lessac-medium   — English fallback so /tts never 404s
set -euo pipefail

MODELS_DIR="$(cd "$(dirname "$0")/.." && pwd)/models"
mkdir -p "$MODELS_DIR"

BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0"

download() {
    local rel="$1"
    local name
    name="$(basename "$rel")"
    if [[ ! -f "$MODELS_DIR/$name.onnx" ]]; then
        echo "downloading $name.onnx ..."
        curl -L --fail --retry 3 -o "$MODELS_DIR/$name.onnx" "$BASE/$rel.onnx?download=true"
    else
        echo "$name.onnx present"
    fi
    if [[ ! -f "$MODELS_DIR/$name.onnx.json" ]]; then
        echo "downloading $name.onnx.json ..."
        curl -L --fail --retry 3 -o "$MODELS_DIR/$name.onnx.json" "$BASE/$rel.onnx.json?download=true"
    else
        echo "$name.onnx.json present"
    fi
}

download "hi/hi_IN/pratham/medium/hi_IN-pratham-medium"
download "en/en_US/lessac/medium/en_US-lessac-medium"

echo "voices ready in $MODELS_DIR"
ls -la "$MODELS_DIR"
