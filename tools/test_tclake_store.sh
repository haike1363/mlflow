#!/bin/bash
SHELL_DIR=$(
  cd "$(dirname "$0")" || exit
  pwd
)
cd "${SHELL_DIR}" || exit

set -eu

export TENCENTCLOUD_SECRET_KEY=xxx
export TENCENTCLOUD_SECRET_ID=xxx
python3.9 tclake_store.py

