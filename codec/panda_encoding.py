# -*- coding: utf-8 -*-
"""
BCH Encoding + Sparsification Processing Tool
Function: Reads binary sequence files, groups the data, performs BCH encoding and sparsification, and outputs the processed results
"""
import argparse
import os
import pickle
import numpy as np
from bch_codes import bchencode
from sparse import sparse_seq


def validate_file_path(path, is_input=True):
    """Validate file path validity"""
    if is_input and not os.path.exists(path):
        raise FileNotFoundError(f"Input file does not exist: {path}")
    # Check if output directory exists, create if not
    output_dir = os.path.dirname(path)
    if output_dir and not os.path.exists(output_dir) and not is_input:
        os.makedirs(output_dir, exist_ok=True)
    return path


def process_binary_data(
    input_bin_file,
    output_seed_file,
    output_encoded_file,
    group_length=91
):
    """
    Core processing function: Reads binary sequence, groups data, performs BCH encoding, 
    sparsification and saves results
    
    Parameters:
    input_bin_file: Path to input binary sequence file (e.g. binary_info.txt)
    output_seed_file: Path to output seed pkl file (e.g. seed.pkl)
    output_encoded_file: Path to output txt file with sparsified encoded sequence (e.g. encoded_info.txt)
    group_length: Group length, default 91
    """
    # Validate file paths
    input_bin_file = validate_file_path(input_bin_file, is_input=True)
    output_seed_file = validate_file_path(output_seed_file, is_input=False)
    output_encoded_file = validate_file_path(output_encoded_file, is_input=False)

    # Step 1: Read binary sequence file
    print(f"Reading input file: {input_bin_file}")
    with open(input_bin_file, 'r', encoding='utf-8') as f:
        info = f.read().strip()  # Remove leading/trailing whitespace characters
    
    if not info:
        raise ValueError("Input file is empty, please check the input file content")
    
    # Step 2: Group processing (padding with 0 to align)
    print(f"Starting group processing, group length: {group_length}")
    n_of_group = int(np.ceil(len(info) / group_length))
    grouped_info = []
    
    for i in range(n_of_group):
        start_idx = group_length * i
        end_idx = group_length * (i + 1)
        group = info[start_idx:end_idx]
        # Pad last group with 0 to align length
        if len(group) < group_length:
            group += '0' * (group_length - len(group))
        grouped_info.append(group)
    
    print(f"Grouping completed, generated {len(grouped_info)} groups of data")

    # Step 3: BCH encoding
    print("Starting BCH encoding...")
    encoded = []
    for idx, group in enumerate(grouped_info):
        try:
            encoded_seq = bchencode(group)
            encoded.append(encoded_seq)
            if (idx + 1) % 100 == 0:  # Print progress every 100 groups
                print(f"BCH encoding progress: {idx+1}/{len(grouped_info)}")
        except Exception as e:
            raise RuntimeError(f"Failed to perform BCH encoding on group {idx}: {str(e)}")

    # Step 4: Sparsification processing
    print("Starting sparsification processing...")
    seed_list = []
    sparsed_list = []
    
    for idx, enc_seq in enumerate(encoded):
        try:
            s, seq = sparse_seq(enc_seq)
            seed_list.append(s)
            sparsed_list.append(seq)
            if (idx + 1) % 100 == 0:  # Print progress every 100 groups
                print(f"Sparsification progress: {idx+1}/{len(encoded)}")
            print(f"\rProcessing progress: {idx+1}/{len(encoded)}", end='', flush=True)
        except Exception as e:
            raise RuntimeError(f"Failed to sparsify group {idx}: {str(e)}")
    print("\nSparsification processing completed")

    # Step 5: Save result files
    print(f"Saving seed file to: {output_seed_file}")
    with open(output_seed_file, 'wb') as f:
        pickle.dump(seed_list, f)
    
    print(f"Saving encoded file to: {output_encoded_file}")
    with open(output_encoded_file, 'w', encoding='utf-8') as f2:
        for line in sparsed_list:
            f2.write(line)
            f2.write('\n')
    
    print("All processing completed!")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="BCH Encoding + Sparsification Processing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
1. Basic usage:
   python bch_sparse_tool.py -i binary_info.txt -s seed.pkl -e encoded_info.txt
   
2. Custom group length:
   python bch_sparse_tool.py -i ./data/bin.txt -s ./output/seed.pkl -e ./output/encoded.txt -g 100
        """
    )
    
    # Core parameters
    parser.add_argument('-i', '--input', 
                        required=True, 
                        help='Path to input binary sequence file (required, e.g. binary_info.txt)')
    parser.add_argument('-s', '--seed', 
                        required=True, 
                        help='Path to output seed pkl file (required, e.g. seed.pkl)')
    parser.add_argument('-e', '--encoded', 
                        required=True, 
                        help='Path to output txt file with sparsified encoded sequence (required, e.g. encoded_info.txt)')
    parser.add_argument('-g', '--group-length', 
                        type=int, 
                        default=91, 
                        help='Group length, default 91')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Execute processing logic
    try:
        process_binary_data(
            input_bin_file=args.input,
            output_seed_file=args.seed,
            output_encoded_file=args.encoded,
            group_length=args.group_length
        )
    except Exception as e:
        print(f"\nProcessing failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()