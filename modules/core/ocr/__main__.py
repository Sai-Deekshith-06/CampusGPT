import argparse
import sys
import os

from .ocr import OCR

def main():
    parser = argparse.ArgumentParser(description="Process a PDF file and convert it to Markdown using OCR.")
    parser.add_argument("input_file", help="Path to the input PDF document")
    parser.add_argument("output_file", help="Path where the processed Markdown file will be stored")
    parser.add_argument("--page-range", help="Optional page range to process (e.g., '1-5')", default=None)
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)
        
    try:
        print(f"Initializing OCR Processor...")
        processor = OCR()
        print(f"Processing '{args.input_file}'...")
        processor.process_file(
            file_path=args.input_file,
            output_path=args.output_file,
            page_range=args.page_range
        )
        print(f"Done! Processed file saved to '{args.output_file}'")
    except Exception as e:
        print(f"An error occurred during OCR processing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
