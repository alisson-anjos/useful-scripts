import os
import re
import sys
import argparse
from collections import Counter

def analyze_txt_files(folder_path):
    """
    Iterates through all .txt files in the specified folder,
    counts word frequencies, and returns a ranking of those frequencies.
    """
    word_counter = Counter()
    
    # Iterate over all files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            
            # Read the contents of each .txt file
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Extract words, ignore punctuation, and convert to lowercase
                words = re.findall(r'\w+', content.lower())
                
                # Update the word counter
                word_counter.update(words)
    
    # Return a list of tuples (word, frequency) sorted by frequency (descending)
    return word_counter.most_common()

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(
        description="Analyze word frequencies in .txt files from a specified folder."
    )
    parser.add_argument(
        "folder_path",
        help="Path to the folder containing .txt files."
    )
    
    # Parse the command-line arguments
    args = parser.parse_args()
    folder_path = args.folder_path

    # Call the function to analyze the .txt files
    ranking = analyze_txt_files(folder_path)
    
    # Print the ranking
    print("Word Frequency Ranking (from most frequent to least frequent):\n")
    for i, (word, freq) in enumerate(ranking, start=1):
        print(f"{i:>3} - '{word}' appeared {freq} times")

if __name__ == '__main__':
    main()
