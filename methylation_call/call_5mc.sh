#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: bash methylation_call/call_5mc.sh READS_DIR OUTPUT_DIR REFERENCE_FASTA [R10.4.1|R9.4.1]

R10.4.1: POD5 reads, Dorado and Modkit.
R9.4.1: FAST5 reads, Megalodon with a Guppy CpG 5mC model, and Modkit.
If the chemistry is omitted, it is selected from the read file extension.
Both paths also require samtools and Python.

Optional variables: THREADS (default 4), DORADO_DEVICE, DORADO_MODEL
(default sup,5mCG_5hmCG), GUPPY_CONFIG, GUPPY_MODELS_DIR and GUPPY_SERVER.
Outputs are written to OUTPUT_DIR/calls.
EOF
}

if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
    usage
    exit 0
fi
if (( $# < 3 || $# > 4 )); then
    usage >&2
    exit 2
fi

reads=$1
output_dir=$2
reference=$3
chemistry=${4:-}
threads=${THREADS:-4}
[[ -d "$reads" && -f "$reference" ]] || {
    echo "Provide an existing reads directory and reference FASTA." >&2
    exit 2
}
[[ "$threads" =~ ^[1-9][0-9]*$ ]] || { echo "THREADS must be a positive integer." >&2; exit 2; }
if [[ -z "$chemistry" ]]; then
    pod5=$(find "$reads" -type f -iname '*.pod5' -print -quit)
    fast5=$(find "$reads" -type f -iname '*.fast5' -print -quit)
    if [[ -n "$pod5" && -z "$fast5" ]]; then
        chemistry=R10.4.1
    elif [[ -n "$fast5" && -z "$pod5" ]]; then
        chemistry=R9.4.1
    else
        echo "Specify the flow cell chemistry when the input format is mixed or unclear." >&2
        exit 2
    fi
fi
case "$chemistry" in
    R10.4.1) basecaller=dorado; extension=pod5 ;;
    R9.4.1) basecaller=megalodon; extension=fast5 ;;
    *) echo "Unsupported flow cell chemistry: $chemistry" >&2; exit 2 ;;
esac
[[ -n "$(find "$reads" -type f -iname "*.$extension" -print -quit)" ]] || {
    echo "$chemistry requires .$extension reads in $reads." >&2
    exit 2
}
for tool in "$basecaller" samtools modkit python; do
    command -v "$tool" >/dev/null 2>&1 || { echo "Required command not found: $tool" >&2; exit 127; }
done

mkdir -p -- "$output_dir"
result="$output_dir/calls"
[[ ! -e "$result" ]] || { echo "Output already exists: $result" >&2; exit 2; }
work=$(mktemp -d "$output_dir/.5mc.XXXXXXXX")
trap 'rm -rf -- "$work"' EXIT

if [[ "$chemistry" == R10.4.1 ]]; then
    dorado_args=(basecaller "${DORADO_MODEL:-sup,5mCG_5hmCG}" "$reads"
        --recursive --reference "$reference" --modified-bases-threshold 0)
    if [[ -n "${DORADO_DEVICE:-}" ]]; then
        dorado_args+=(--device "$DORADO_DEVICE")
    fi
    dorado "${dorado_args[@]}" | samtools sort -@ "$threads" -o "$work/aligned.bam" -
    dorado summary "$work/aligned.bam" > "$work/sequencing_summary.tsv"
else
    megalodon_args=("$reads" --reference "$reference" --mod-motif m CG 0
        --outputs mappings mod_mappings --output-directory "$work/megalodon"
        --guppy-config "${GUPPY_CONFIG:-res_dna_r941_min_modbases_5mC_CpG_v001.cfg}"
        --processes "$threads")
    if [[ -n "${GUPPY_MODELS_DIR:-}" ]]; then
        megalodon_args+=(--guppy-params "-d $GUPPY_MODELS_DIR")
    fi
    if [[ -n "${GUPPY_SERVER:-}" ]]; then
        megalodon_args+=(--guppy-server-path "$GUPPY_SERVER")
    fi
    megalodon "${megalodon_args[@]}"
    samtools sort -@ "$threads" -o "$work/aligned.bam" "$work/megalodon/mod_mappings.bam"
fi

samtools index -@ "$threads" "$work/aligned.bam"
modkit extract full "$work/aligned.bam" "$work/modkit.tsv" \
    --mapped-only --threads "$threads"

# Preserve 5mC probabilities, including zero probabilities and zero-based positions.
# The output uses the same column names as the existing clustering script.
python - "$work/modkit.tsv" "$work/per_read_5mc.tsv" <<'PYTHON'
import csv
import math
import sys

source, destination = sys.argv[1:]
required = {"read_id", "chrom", "ref_position", "mod_code", "mod_qual"}
with open(source, encoding="utf-8", newline="") as raw, open(
    destination, "w", encoding="utf-8", newline=""
) as out:
    rows = csv.DictReader(raw, delimiter="\t")
    if not required.issubset(rows.fieldnames or ()):
        sys.exit("Unexpected Modkit extract format. Missing required columns.")
    writer = csv.writer(out, delimiter="\t", lineterminator="\n")
    writer.writerow(["read_id", "chrm", "pos", "mod_log_prob"])
    count = 0
    for row in rows:
        if row["mod_code"] != "m":
            continue
        pos = int(row["ref_position"])
        if pos < 0 or row["chrom"] == ".":
            continue
        probability = float(row["mod_qual"])
        if not 0 <= probability <= 1:
            sys.exit(f"Invalid 5mC probability for read {row['read_id']}: {probability}")
        writer.writerow([row["read_id"], row["chrom"], pos,
                         math.log(probability) if probability else "-inf"])
        count += 1
    if not count:
        sys.exit("No mapped 5mC probabilities were found. Check the model and reference.")
PYTHON

rm -- "$work/modkit.tsv"
# Atomic directory rename, with no replacement of an existing result.
python - "$work" "$result" <<'PYTHON'
import os
import sys
from pathlib import Path

source, destination = map(Path, sys.argv[1:])
if os.path.lexists(destination):
    sys.exit(f"Output already exists: {destination}")
source.rename(destination)
PYTHON
trap - EXIT
printf '5mC results written to %s\n' "$result"
