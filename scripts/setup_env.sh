#!/usr/bin/env bash
# setup_env.sh — idempotent .env bootstrap for one-command turnup.
# - If .env is a valid symlink to an existing file: keep it.
# - If .env is missing or a broken symlink: create/replace with copy of .env.example.
# - If .env already exists as a regular file: do nothing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [ -L .env ] && [ -e .env ]; then
  echo ".env symlink valid -> $(readlink .env) (kept)"
  exit 0
fi

if [ -L .env ] && [ ! -e .env ]; then
  echo ".env symlink broken -> $(readlink .env) (replacing)"
  rm .env
fi

if [ -f .env ]; then
  echo ".env exists (kept)"
  exit 0
fi

if [ -f .env.example ]; then
  cp .env.example .env
  echo ".env created from .env.example"
else
  echo "ERROR: .env.example not found" >&2
  exit 1
fi
