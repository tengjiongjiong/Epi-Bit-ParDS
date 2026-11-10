Epi-Bit-ParDS file encoding and recovery

From the codec directory, install the dependencies:

    python -m pip install numpy pyfinite

To encode an existing image or compressed archive, use --input-format file.
The encoder reads the original bytes, so JPEG, PNG, AVIF, ZIP, and other
binary file formats use the same BCH and sparsification steps. To reduce
the size of an image before encoding, use the optional AVIF conversion
described below. Use a file size that fits the experimental capacity.

Encode an image or a ZIP archive:

    python panda_encoding.py -i panda.avif --input-format file --pvs-output panda_encoded.csv
    python panda_encoding.py -i sample.zip --input-format file --pvs-output zip_encoded.csv

Record the original byte count printed by the encoder and keep the file
extension. The PVS output is a headerless CSV with the interleaved,
sparsified 234-bit payloads and their seeds in storage order. For a
software round trip, pass that CSV directly to the decoder. After
sequencing, supply the recovered rows in the same order, with payload
and seed as the first two columns. Extra columns are ignored.

    python panda_decoding.py -i panda_encoded.csv -o panda_recovered.avif --size 7882

For a ZIP archive, replace SIZE_IN_BYTES with the count printed by the
encoder for sample.zip:

    python panda_decoding.py -i zip_encoded.csv -o sample_recovered.zip --size SIZE_IN_BYTES

The size excludes BCH and template padding. If the source file is
available, compare its SHA-256 hash with the recovered file. A recovered
ZIP can also be checked with:

    python -m zipfile -t sample_recovered.zip

The bundled pvs.csv contains results obtained from nanopore sequencing.
Run the following command from the codec directory to reproduce the
original panda_deco.avif output:

    python panda_decoding.py

Existing bit-text and AVIF workflows

The existing 0/1 input and separate seed and codeword output still work:

    python panda_encoding.py -i binary_info.txt -s seed.pkl -e encoded_info.txt

To convert a JPG to a smaller AVIF before encoding, install Pillow and
pillow-avif-plugin and run:

    python -m pip install Pillow pillow-avif-plugin
    python transform_figure_format.py img2avif -i panda.jpg -o compressed.avif

Use compressed.avif as the file input to the encoder. The recovered file
will be the AVIF that was encoded. Use the original JPG as file input
if you need to recover the original JPG bytes.

The original AVIF-to-bit-text command is also available:

    python transform_figure_format.py avif2txt -i panda.avif -o binary_info_wrapped.txt

AVIF files can be opened in a supporting browser. The repository includes
the BCH implementation based on https://github.com/NovosadVictor/BCH-codes.
