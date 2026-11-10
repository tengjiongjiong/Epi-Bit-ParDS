# Epi-Bit-ParDS

Run these commands from the repository root on Linux.

```bash
bash Build_environment.sh
conda activate Epi-env
```

## Encoding and sequencing

See [codec/README.txt](codec/README.txt) for image and ZIP encoding with `codec/encoding.py`. Keep the original byte count, the payload order and the sparsification seeds.

Open [QC.ipynb](data_analysis/QC.ipynb) in JupyterLab and set `SUMMARY_PATH` to a tab-separated sequencing summary. For R10.4.1 data, the calling script can also generate a Dorado summary.

```bash
bash methylation_call/call_5mc.sh reads_pod5 output reference.fasta R10.4.1
```

Install Dorado and Modkit separately and make their executables available on `PATH`. For legacy R9.4.1 runs, use a FAST5 directory and specify `R9.4.1`. Install Megalodon and a compatible Guppy CpG 5mC model for that route. Run `bash methylation_call/call_5mc.sh --help` for model and device overrides.

The script writes a sorted, indexed BAM and `per_read_5mc.tsv` under `output/calls`. R10.4.1 also writes `sequencing_summary.tsv`. Use a separate output directory for each run.

## Data recovery

Open [analysis.ipynb](data_analysis/analysis.ipynb) in JupyterLab. The default example decodes the bundled panda sequencing PVS. For your own file, enter its original byte count, output extension and either an ordered PVS file or the per-read 5mC table, write layout and read-to-payload assignments. The notebook documents the CSV schemas and the optional calibration and clustering inputs.

For optional dynamic clustering of the original L1–L5 design, use the actual input options:

```bash
python data_analysis/dynamic_clustering.py -p output/calls/per_read_5mc.tsv -bp barcode_sites.csv -cp barcode_codes.csv -op clustered
```

The position CSV uses `chrom,pos` and the code CSV uses `chrom,barcode,info`. Preserve leading zeroes in barcodes. To use clustered assignments in the recovery notebook, supply the chosen `iter_N` directory and a `cluster_index,row` mapping for your write design.
