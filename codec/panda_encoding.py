# -*- coding: utf-8 -*-
"""Encode a bit-text file or a raw file using BCH and sparsification."""

import argparse
import csv
import pickle
from pathlib import Path

from bch_codes import DATA_BITS, bchencode
from sparse import sparse_seq


PVS_PAYLOAD_BITS = 234


def process_binary_data(
    input_bin_file,
    output_seed_file=None,
    output_encoded_file=None,
    group_length=DATA_BITS,
    *,
    input_format="bits",
    output_pvs_file=None,
):
    """Write legacy sparsified BCH blocks or interleaved payloads with seeds."""
    if output_pvs_file is None:
        if output_seed_file is None or output_encoded_file is None:
            raise ValueError("Provide both the seed file and the encoded file.")
        output_paths = [Path(output_seed_file), Path(output_encoded_file)]
    else:
        if output_seed_file is not None or output_encoded_file is not None:
            raise ValueError("Use either PVS output or the seed and encoded files.")
        if group_length != DATA_BITS:
            raise ValueError(f"PVS output requires {DATA_BITS}-bit BCH input blocks.")
        output_paths = [Path(output_pvs_file)]

    if group_length <= 0:
        raise ValueError("Group length must be positive.")

    input_path = Path(input_bin_file)
    if len({path.resolve() for path in [input_path, *output_paths]}) != 1 + len(output_paths):
        raise ValueError("Input and output paths must be distinct.")

    if input_format == "file":
        data = input_path.read_bytes()
        info = "".join(f"{byte:08b}" for byte in data)
    elif input_format == "bits":
        info = "".join(input_path.read_text(encoding="utf-8").split())
    else:
        raise ValueError(f"Unknown input format: {input_format}")

    if not info or set(info) - {"0", "1"}:
        raise ValueError("Input must contain a nonempty sequence of 0 and 1 bits.")

    encoded = [
        bchencode(info[start:start + group_length].ljust(group_length, "0"))
        for start in range(0, len(info), group_length)
    ]

    if output_pvs_file is not None:
        # Interleave BCH codewords before splitting them into template payloads.
        stream = "".join("".join(column) for column in zip(*encoded))
        encoded = [
            stream[start:start + PVS_PAYLOAD_BITS].ljust(PVS_PAYLOAD_BITS, "0")
            for start in range(0, len(stream), PVS_PAYLOAD_BITS)
        ]

    rows = []
    for index, sequence in enumerate(encoded, start=1):
        result = sparse_seq(sequence)
        if result is False:
            raise RuntimeError(f"No sparsification seed found for row {index}.")
        seed, bits = result
        rows.append((bits, seed))

    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)

    if output_pvs_file is not None:
        with output_paths[0].open("w", encoding="utf-8", newline="") as output:
            csv.writer(output).writerows(rows)
    else:
        seed_path, encoded_path = output_paths
        with seed_path.open("wb") as output:
            pickle.dump([seed for _, seed in rows], output)
        with encoded_path.open("w", encoding="utf-8") as output:
            for bits, _ in rows:
                output.write(bits + "\n")

    print(f"Encoded {len(info)} bits into {len(rows)} rows.")
    if input_format == "file":
        print(f"Original file size: {len(info) // 8} bytes. Record this for decoding.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-i", "--input", required=True, help="Input file path")
    parser.add_argument(
        "--input-format",
        choices=("bits", "file"),
        default="bits",
        help="Read 0/1 text (default) or the original bytes of an image, archive, or other file",
    )
    parser.add_argument("-s", "--seed", help="Legacy output file for the pickle seed list")
    parser.add_argument("-e", "--encoded", help="Legacy output file for sparsified BCH blocks")
    parser.add_argument(
        "--pvs-output", help="Output CSV with interleaved payloads and seeds for sequencing-style decoding"
    )
    parser.add_argument("-g", "--group-length", type=int, default=DATA_BITS, help="BCH input block length")
    args = parser.parse_args()

    try:
        process_binary_data(
            args.input,
            args.seed,
            args.encoded,
            args.group_length,
            input_format=args.input_format,
            output_pvs_file=args.pvs_output,
        )
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Encoding failed: {error}\n")


if __name__ == "__main__":
    main()
