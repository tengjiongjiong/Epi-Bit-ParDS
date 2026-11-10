#!/usr/bin/env bash
set -euo pipefail

repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if ! command -v conda >/dev/null 2>&1; then
    echo "Install Miniconda or Anaconda and make conda available on PATH." >&2
    exit 1
fi

conda env update --name Epi-env --file "$repo_dir/environment.yml"
printf '\nActivate the environment with: conda activate Epi-env\n'
