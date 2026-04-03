# -*- coding: utf-8 -*-
"""
AVIF Format Conversion Tool
Supports:
1. Convert AVIF to JPEG/PNG
2. Convert other image formats to AVIF
3. Convert AVIF binary stream to 0/1 sequence text file
"""
import argparse
import os
from PIL import Image
import pillow_avif

# Ensure pillow-avif-plugin is installed (add check in code)
try:
    from pillow_avif import AvifImagePlugin
except ImportError:
    raise ImportError("Please install the dependency first: pip install pillow-avif-plugin")


def avif_to_image(input_path: str, output_path: str, format: str = 'JPEG') -> None:
    """
    Convert AVIF file to JPEG/PNG format
    
    Args:
        input_path: Input AVIF file path
        output_path: Output image file path
        format: Output format, options: JPEG/PNG
    """
    try:
        with Image.open(input_path) as img:
            # Ensure RGB mode (JPEG doesn't support RGBA)
            if format.upper() == 'JPEG' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(output_path, format)
        print(f"✅ AVIF conversion completed: {output_path}")
    except Exception as e:
        print(f"❌ Conversion failed: {e}")


def image_to_avif(input_path: str, output_path: str) -> None:
    """
    Convert other image formats to AVIF
    
    Args:
        input_path: Input image file path
        output_path: Output AVIF file path
    """
    try:
        with Image.open(input_path) as img:
            img.save(output_path, 'AVIF')
        print(f"✅ Image to AVIF conversion completed: {output_path}")
    except Exception as e:
        print(f"❌ Conversion failed: {e}")


def avif_to_binary_txt(input_path: str, output_path: str, bytes_per_line: int = 16) -> None:
    """
    Convert AVIF file's binary stream directly to 0/1 sequence text file
    Principle: Read each byte of the file, convert to 8-bit binary string (0-padded),
               then write to text file with specified bytes per line
    
    Args:
        input_path: Input AVIF file path
        output_path: Output text file path
        bytes_per_line: Number of bytes to display per line (default: 16)
    """
    try:
        # Check if input file exists
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read AVIF file as binary stream
        with open(input_path, 'rb') as f:
            binary_data = f.read()
        
        # Convert binary data to 0/1 sequence
        binary_str = ""
        line_count = 0
        for byte in binary_data:
            # Convert single byte to 8-bit binary string (0-padded)
            # bin(255) -> '0b11111111' -> [2:] to remove '0b' prefix
            # zfill(8) ensures 8 bits even for small numbers (e.g., 0 -> '00000000')
            byte_binary = bin(byte)[2:].zfill(8)
            binary_str += byte_binary
            
            # Add newline after specified number of bytes
            line_count += 1
            if line_count % bytes_per_line == 0:
                binary_str += '\n'
        
        # Remove trailing newline if exists (for clean output)
        if binary_str and binary_str[-1] == '\n':
            binary_str = binary_str[:-1]
        
        # Save 0/1 sequence to text file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(binary_str)
        
        # Print conversion summary
        file_size = len(binary_data)
        total_bits = file_size * 8
        print(f"✅ AVIF binary stream to 0/1 sequence completed: {output_path}")
        print(f"📄 File size: {file_size} bytes ({total_bits} bits)")
        print(f"📏 Format: {bytes_per_line} bytes per line (each byte = 8 bits)")
        
    except Exception as e:
        print(f"❌ Conversion failed: {e}")


def main():
    # Create command line argument parser
    parser = argparse.ArgumentParser(description='AVIF Format Conversion Tool', formatter_class=argparse.RawTextHelpFormatter)
    
    # Subcommand settings
    subparsers = parser.add_subparsers(dest='command', help='Operation types:\n  avif2img - Convert AVIF to image\n  img2avif - Convert image to AVIF\n  avif2txt - Convert AVIF binary stream to 0/1 sequence')
    
    # 1. AVIF to image subcommand
    parser_avif2img = subparsers.add_parser('avif2img', help='Convert AVIF to JPEG/PNG')
    parser_avif2img.add_argument('-i', '--input', required=True, help='Input AVIF file path')
    parser_avif2img.add_argument('-o', '--output', required=True, help='Output image file path (suffix: jpg/png)')
    parser_avif2img.add_argument('-f', '--format', default='JPEG', choices=['JPEG', 'PNG'], help='Output format (default: JPEG)')
    
    # 2. Image to AVIF subcommand
    parser_img2avif = subparsers.add_parser('img2avif', help='Convert other image formats to AVIF')
    parser_img2avif.add_argument('-i', '--input', required=True, help='Input image file path')
    parser_img2avif.add_argument('-o', '--output', required=True, help='Output AVIF file path')
    
    # 3. AVIF to 0/1 sequence subcommand (updated parameters)
    parser_avif2txt = subparsers.add_parser('avif2txt', help='Convert AVIF binary stream to 0/1 sequence text file')
    parser_avif2txt.add_argument('-i', '--input', required=True, help='Input AVIF file path')
    parser_avif2txt.add_argument('-o', '--output', required=True, help='Output text file path')
    parser_avif2txt.add_argument('-b', '--bytes_per_line', type=int, default=16, help='Bytes per line (default: 16)')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if input file exists
    if args.command in ['avif2img', 'avif2txt']:
        if not os.path.exists(args.input) or not args.input.lower().endswith('.avif'):
            print(f"❌ Input file does not exist or is not AVIF format: {args.input}")
            return
    elif args.command == 'img2avif':
        if not os.path.exists(args.input):
            print(f"❌ Input file does not exist: {args.input}")
            return
    
    # Execute corresponding operation
    if args.command == 'avif2img':
        avif_to_image(args.input, args.output, args.format)
    elif args.command == 'img2avif':
        image_to_avif(args.input, args.output)
    elif args.command == 'avif2txt':
        avif_to_binary_txt(args.input, args.output, args.bytes_per_line)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()