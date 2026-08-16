#!/usr/bin/env python3
"""
Standalone STT verification script for mlx-whisper.
Tests model loading and single-file transcription with timing and metadata.
"""

import argparse
import os
import sys
import time
import mlx.core as mx
import mlx_whisper
from mlx_whisper.load_models import load_model

DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"


def check_acceleration() -> dict:
    default_dev = mx.default_device()
    metal_avail = mx.metal.is_available()
    return {
        "default_device": str(default_dev),
        "metal_available": metal_avail,
        "is_gpu": default_dev.type == mx.Device.gpu if hasattr(mx.Device, "gpu") else "gpu" in str(default_dev),
    }


def verify_model_load(model_name: str = DEFAULT_MODEL):
    accel = check_acceleration()
    print("=" * 60)
    print("MLX HARDWARE ACCELERATION STATUS:")
    print(f"  - Default Device:    {accel['default_device']}")
    print(f"  - Metal Available:   {accel['metal_available']}")
    print(f"  - GPU Active:        {accel['is_gpu']}")
    print("=" * 60)

    if not accel["metal_available"] or not accel["is_gpu"]:
        print("WARNING: Metal GPU acceleration does NOT appear to be active. MLX may run on CPU.")

    print(f"\nLoading model: {model_name} ...")
    start_time = time.perf_counter()
    model = load_model(model_name)
    load_duration = time.perf_counter() - start_time

    print(f"Model loaded successfully in {load_duration:.4f} seconds ({load_duration*1000:.2f} ms).")
    print(f"Model type: {type(model).__name__}")
    print("=" * 60)
    return model, load_duration


def transcribe_file(audio_path: str, model_name: str = DEFAULT_MODEL):
    if not os.path.exists(audio_path):
        print(f"ERROR: Audio file not found at path: {audio_path}", file=sys.stderr)
        sys.exit(1)

    accel = check_acceleration()
    print("=" * 60)
    print("MLX HARDWARE ACCELERATION STATUS:")
    print(f"  - Default Device:    {accel['default_device']}")
    print(f"  - Metal Available:   {accel['metal_available']}")
    print(f"  - GPU Active:        {accel['is_gpu']}")
    print("=" * 60)

    print(f"\nTarget audio file: {audio_path}")
    print(f"File size:         {os.path.getsize(audio_path)} bytes")
    print(f"Using model:       {model_name}")

    print("\n[1/2] Loading model...")
    load_start = time.perf_counter()
    # load_model pre-warms cache / downloads weights if needed
    _ = load_model(model_name)
    load_duration = time.perf_counter() - load_start
    print(f"Model load/verify time: {load_duration:.4f}s")

    print("\n[2/2] Running transcription...")
    transcribe_start = time.perf_counter()
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=model_name,
        verbose=False,
    )
    transcribe_duration = time.perf_counter() - transcribe_start

    print("\n" + "=" * 60)
    print("TRANSCRIPTION RESULTS:")
    print("=" * 60)
    print(f"Transcribed Text:\n{result.get('text', '').strip()}")
    print("-" * 60)
    print(f"Detected Language:        {result.get('language', 'unknown')}")
    print(f"Transcription Time:       {transcribe_duration:.4f} seconds ({transcribe_duration*1000:.2f} ms)")
    print(f"Model Load Time:          {load_duration:.4f} seconds ({load_duration*1000:.2f} ms)")
    print(f"Total Wall-Clock Time:    {(load_duration + transcribe_duration):.4f} seconds")

    segments = result.get("segments", [])
    if segments:
        print("-" * 60)
        print(f"Segments ({len(segments)} total):")
        for i, seg in enumerate(segments):
            print(f"  [{i+1}] ({seg.get('start', 0.0):.2f}s -> {seg.get('end', 0.0):.2f}s): \"{seg.get('text', '').strip()}\"")
            print(f"      avg_logprob:         {seg.get('avg_logprob', 'N/A')}")
            print(f"      no_speech_prob:      {seg.get('no_speech_prob', 'N/A')}")
            print(f"      compression_ratio:   {seg.get('compression_ratio', 'N/A')}")
    print("=" * 60)
    return result


def main():
    parser = argparse.ArgumentParser(description="Verify mlx-whisper STT model loading and transcription.")
    parser.add_argument("audio_file", nargs="?", default=None, help="Path to audio file to transcribe (optional)")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model repository (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if args.audio_file:
        transcribe_file(args.audio_file, model_name=args.model)
    else:
        print("No audio file provided. Running model load verification only.")
        verify_model_load(model_name=args.model)


if __name__ == "__main__":
    main()
