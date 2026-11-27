#!/usr/bin/env bash
# Download REE tasks from Hugging Face and restore their executable bits.
#
#   scripts/fetch.sh all                  every task (66.6 GiB)
#   scripts/fetch.sh <area>               one area: math, physical, life, earth or language
#   scripts/fetch.sh <task> [...]         named tasks, e.g. scripts/fetch.sh seismic_observatory
#
# Tasks land in $DATA_DIR/tasks/<task> (default ./REE). Set REVISION to pin a revision of the dataset
# (default main) and DRY_RUN=1 to print the download command without running it.
set -euo pipefail

REPO=Tokenwave-AI/REE
REVISION=${REVISION:-main}
DATA_DIR=${DATA_DIR:-REE}
HERE=$(cd "$(dirname "$0")/.." && pwd)
TSV="$HERE/results/paper-v1.tsv"

[ $# -ge 1 ] || { sed -n '2,9p' "$0"; exit 1; }

area_name() {
  case "$1" in
    math) echo "Mathematics & Computing" ;;
    physical) echo "Physical Sciences & Engineering" ;;
    life) echo "Life & Health Sciences" ;;
    earth) echo "Earth & Environmental Sciences" ;;
    language) echo "Language, Society & Culture" ;;
    *) echo "" ;;
  esac
}

includes=(--include executables.txt)
for arg in "$@"; do
  area=$(area_name "$arg")
  if [ "$arg" = all ]; then
    includes+=(--include "tasks/*")
  elif [ -n "$area" ]; then
    while IFS= read -r task; do
      includes+=(--include "tasks/$task/*")
    done < <(awk -F'\t' -v a="$area" 'NR > 1 && $2 == a {print $1}' "$TSV" | sort -u)
  elif awk -F'\t' -v t="$arg" 'NR > 1 && $1 == t {found = 1} END {exit !found}' "$TSV"; then
    includes+=(--include "tasks/$arg/*")
  else
    echo "unknown task or area: $arg (areas: math, physical, life, earth, language)" >&2
    exit 1
  fi
done

if [ "${DRY_RUN:-0}" = 1 ]; then
  printf '%q ' hf download "$REPO" --repo-type dataset --revision "$REVISION" --local-dir "$DATA_DIR" "${includes[@]}"
  echo
  exit 0
fi
hf download "$REPO" --repo-type dataset --revision "$REVISION" --local-dir "$DATA_DIR" "${includes[@]}" > /dev/null

# Hugging Face does not store file modes; executables.txt lists the files that must be executable.
cd "$DATA_DIR"
while IFS= read -r f; do
  if [ -e "$f" ]; then chmod +x "$f"; fi
done < executables.txt
echo "tasks ready in $DATA_DIR/tasks: $(ls tasks | wc -l)"
