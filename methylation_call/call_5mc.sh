#!/usr/bin/env bash

eval "$(conda shell.bash hook)"
conda activate megalodon

input_dir=$1
output_dir=$2
ref=$3

megalodon $1 \
    --output-directory $2/megalodon \
    --reference $3 --mod-motif m CG 0 \
    --outputs basecalls mod_basecalls mappings mod_mappings per_read_mods mods \
    --guppy-params "-d /home/eason/nvme/ont/rerio/basecall_models" \
    --guppy-config res_dna_r941_min_modbases_5mC_CpG_v001.cfg \
    --guppy-server-path /home/eason/nvme/ont/ont-guppy/bin/guppy_basecall_server \
    --devices cuda:0 --processes 4 --overwrite \
    > /dev/null 2>&1
