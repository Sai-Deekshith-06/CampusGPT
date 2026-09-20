import os
import logging
from dotenv import load_dotenv

# Suppress annoying SDK warnings
logging.getLogger("google.genai").setLevel(logging.ERROR)

from .parse import parse_pdf

class OCR:
    """
    OCR class to handle converting PDF files to Markdown.
    Uses the underlying parse module.
    This class is designed to be used in the file manager for CampusGPT.
    """
    
    def __init__(self, api_key: str = None):
        """
        Initializes the OCR class.
        If api_key is not provided, it will be loaded from the .env file.
        """
        load_dotenv()
        
        self.api_key = api_key or os.getenv("API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI API_KEY is not set. Please provide it or set it in your .env file.")
            
    def _log_callback(self, msg: str):
        """
        Callback for logging messages from the pdf parser.
        """
        print(f"[OCR] {msg.strip()}")

    def process_file(self, 
                     file_path: str, 
                     output_path: str = None, 
                     page_range: str = None, 
                     custom_prompt: str = None) -> str:
        """
        Processes a single PDF file and returns the generated markdown text.
        
        Args:
            file_path (str): The absolute or relative path to the PDF file.
            output_path (str, optional): The path to save the generated markdown file.
            page_range (str, optional): The pages to parse, e.g., '1-5'.
            custom_prompt (str, optional): A custom prompt for the OCR process.
            
        Returns:
            str: The generated markdown text.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The PDF file was not found: {file_path}")
            
        print(f"[OCR] Starting processing for {file_path}")
        
        try:
            # If output_path is a directory, construct the file path automatically
            if output_path and (os.path.isdir(output_path) or output_path.endswith(os.sep) or output_path.endswith('/')):
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join(output_path, f"{base_name}.md")
                
            markdown_text = parse_pdf(
                api_key=self.api_key,
                file_path=file_path,
                log_callback=self._log_callback,
                custom_prompt=custom_prompt,
                page_range=page_range,
                output_path=output_path
            )
            
            if output_path:
                # Ensure the output directory exists
                out_dir = os.path.dirname(output_path)
                if out_dir:
                    os.makedirs(out_dir, exist_ok=True)
                    
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(markdown_text)
                print(f"[OCR] Successfully saved markdown to {output_path}")
                
            return markdown_text
            
        except Exception as e:
            print(f"[OCR] Error during PDF processing: {e}")
            raise
