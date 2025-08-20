import os
import argparse
from collections import Counter

def count_tags_in_folder(folder):
    tag_counter = Counter()

    for filename in os.listdir(folder):
        if filename.endswith(".txt"):
            filepath = os.path.join(folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    tags = [tag.strip() for tag in line.strip().split(",") if tag.strip()]
                    tag_counter.update(tags)

    return tag_counter

def main():
    parser = argparse.ArgumentParser(description="Count the frequency of tags in .txt files inside a folder.")
    parser.add_argument("folder", type=str, help="Path to the folder containing .txt files")

    args = parser.parse_args()
    result = count_tags_in_folder(args.folder)

    print("\nTags found:")
    for tag, count in result.most_common():
        print(f"{tag}: {count}")

if __name__ == "__main__":
    main()
