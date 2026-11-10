# -*- coding: utf-8 -*-
"""Recover an image, archive, or other file from ordered PVS rows."""

import argparse
import csv
from pathlib import Path

import numpy as np

from bch_codes import CODEWORD_BITS, DATA_BITS, bchdecode


def resparse(seq, seed):
    """Reverse the random mask used by sparse_seq."""
    mask = np.random.RandomState(seed).randint(2, size=len(seq))
    return "".join(str(int(bit) ^ mask_bit) for bit, mask_bit in zip(seq, mask))


def decode_file(input_csv, output_file, size_bytes):
    """Decode headerless rows whose first two columns are bits and seed."""
    if size_bytes <= 0:
        raise ValueError("The original file size must be a positive number of bytes.")

    input_path = Path(input_csv)
    output_path = Path(output_file)
    if input_path.resolve() == output_path.resolve():
        raise ValueError("Input and output paths must be distinct.")

    rows = []
    with input_path.open(encoding="utf-8", newline="") as source:
        for index, row in enumerate(csv.reader(source), start=1):
            if len(row) < 2 or not row[0] or set(row[0]) - {"0", "1"}:
                raise ValueError(f"Expected binary payload and seed in CSV row {index}.")
            bits, seed = row[:2]
            if rows and len(bits) != len(rows[0]):
                raise ValueError(f"Unexpected payload length in CSV row {index}.")
            try:
                rows.append(resparse(bits, int(seed)))
            except ValueError as error:
                raise ValueError(f"Invalid seed in CSV row {index}: {seed!r}.") from error

    bit_count = size_bytes * 8
    block_count = (bit_count + DATA_BITS - 1) // DATA_BITS
    stream_length = block_count * CODEWORD_BITS
    if not rows or not (len(rows) - 1) * len(rows[0]) < stream_length <= len(rows) * len(rows[0]):
        raise ValueError("The number of payload rows does not match the original file size.")

    stream = "".join(rows)[:stream_length]
    # Undo the encoder's interleaving to reassemble the BCH codewords.
    codewords = np.fromiter(stream, dtype=np.uint8).reshape(CODEWORD_BITS, block_count).T
    bits = "".join(bchdecode(word) for word in codewords)[:bit_count]
    data = bytes(int(bits[start:start + 8], 2) for start in range(0, bit_count, 8))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(data)
    print(f"Recovered {size_bytes} bytes to {output_path}.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="With no arguments, decode the bundled pvs.csv to panda_deco.avif.",
    )
    parser.add_argument("-i", "--input", help="Headerless CSV of ordered payloads and seeds")
    parser.add_argument("-o", "--output", help="Output file path with the original extension")
    parser.add_argument("--size", type=int, help="Original file size in bytes, before encoding")
    args = parser.parse_args()

    if args.input is None and args.output is None and args.size is None:
        args.input, args.output, args.size = "pvs.csv", "panda_deco.avif", 7882
    elif args.input is None or args.output is None or args.size is None:
        parser.error("Provide --input, --output, and --size together.")

    try:
        decode_file(args.input, args.output, args.size)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Decoding failed: {error}\n")


if __name__ == "__main__":
    main()
