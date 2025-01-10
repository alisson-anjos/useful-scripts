import os
import re
import sys
import glob

def extract_subtitle_text(srt_path: str) -> str:
    """
    Extracts subtitle text from an .srt file by removing:
      - Empty lines
      - Numeric indices
      - Timestamp lines (e.g., '00:00:01,000 --> 00:00:04,000')
      - <font> or any other HTML-like tags
    Returns the extracted text as a single string with line breaks.
    """
    extracted_lines = []

    # Regex for timestamps like "00:00:00,000 --> 00:00:01,699"
    timestamp_pattern = re.compile(r'^\d{2}:\d{2}:\d{2},\d{3}\s-->\s\d{2}:\d{2}:\d{2},\d{3}$')

    with open(srt_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines and numeric indices
            if not line or line.isdigit():
                continue
            # Skip timestamp lines
            if timestamp_pattern.match(line):
                continue
            # Remove any HTML-like tags (e.g., <font color="green"> or <br> or anything in <...>)
            line = re.sub(r'<.*?>', '', line)
            extracted_lines.append(line)

    return "\n".join(extracted_lines)

def convert_srt_to_txt(folder_path: str):
    """
    Iterates through all .srt files in 'folder_path', extracts the text,
    and saves each extracted text in a .txt file with the same base name.
    """
    # Find all .srt files in the specified folder
    srt_files = glob.glob(os.path.join(folder_path, "*.srt"))

    for srt_file in srt_files:
        # Extract text from the SRT file
        text_content = extract_subtitle_text(srt_file)
        
        # Create the corresponding .txt file path
        txt_file = os.path.splitext(srt_file)[0] + ".txt"
        
        # Write the extracted text to the .txt file (UTF-8 encoding)
        with open(txt_file, 'w', encoding='utf-8') as output:
            output.write(text_content)
        
        print(f"Processed '{srt_file}' -> '{txt_file}'")

if __name__ == "__main__":
    # Check if the user provided a folder path as an argument
    if len(sys.argv) < 2:
        print("Usage: python script.py <folder_path>")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    
    # Convert all .srt files in the provided folder path
    convert_srt_to_txt(input_folder)
    
    print("All .srt files have been processed.")
