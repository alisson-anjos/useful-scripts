import csv
import os
import argparse

def process_csv(input_csv, content_column, filename_column, output_dir):
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Process the CSV file
    with open(input_csv, mode='r', encoding='utf-8') as csv_file:
        reader = csv.DictReader(csv_file)
        
        for row in reader:
            # Get content and filename from each row
            content = row.get(content_column, '').strip()
            filename = row.get(filename_column, '').strip()
            
            if content and filename:
                # Remove the file extension and append .txt
                filename = os.path.splitext(filename)[0] + '.txt'
                
                # Create the full file path
                file_path = os.path.join(output_dir, filename)
                
                # Save the content to the file
                with open(file_path, mode='w', encoding='utf-8') as output_file:
                    output_file.write(content)

    print(f'Files have been generated in the directory: {output_dir}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a CSV file to generate files based on specified columns.")
    parser.add_argument('--input_csv', required=True, help="Path to the input CSV file.")
    parser.add_argument('--content_column', required=True, help="Name of the column containing the content for the files.")
    parser.add_argument('--filename_column', required=True, help="Name of the column containing the filenames.")
    parser.add_argument('--output_dir', required=True, help="Directory where the output files will be saved.")

    args = parser.parse_args()

    process_csv(args.input_csv, args.content_column, args.filename_column, args.output_dir)
