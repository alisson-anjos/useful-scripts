import os
import argparse

def prepend_text_to_txt_files(directory_path, text_to_prepend):
    """
    Prepends a given text to all .txt files in the specified directory.

    :param directory_path: Path to the directory containing the .txt files.
    :param text_to_prepend: Text to prepend to each .txt file.
    """
    # Verify the directory exists
    if not os.path.isdir(directory_path):
        print(f"The directory '{directory_path}' does not exist.")
        return

    # Iterate over the files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".txt"):
            file_path = os.path.join(directory_path, filename)

            # Read the current content of the file
            with open(file_path, 'r', encoding='utf-8') as file:
                current_content = file.read()

            # Prepend the text to the current content
            updated_content = text_to_prepend + current_content

            # Write the updated content back to the file
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)

            print(f"Prepended text to: {file_path}")

def main():
    parser = argparse.ArgumentParser(
        description="Prepend text to all .txt files in a specified directory."
    )
    parser.add_argument(
        "directory_path",
        type=str,
        help="Path to the directory containing the .txt files."
    )
    parser.add_argument(
        "text_to_prepend",
        type=str,
        help="The text to prepend to each .txt file."
    )
    
    args = parser.parse_args()
    
    prepend_text_to_txt_files(args.directory_path, args.text_to_prepend)

if __name__ == "__main__":
    main()
