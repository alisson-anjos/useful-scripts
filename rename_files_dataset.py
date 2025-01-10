import os
import sys
from collections import defaultdict
import uuid

def rename_files_in_order(folder_path):
    """
    1) Renames files to guaranteed-unique temporary names.
    2) Then renames them to final sequential names.
    """

    # Collect all files
    try:
        all_files = os.listdir(folder_path)
    except FileNotFoundError:
        print(f"Error: The directory '{folder_path}' does not exist.")
        return

    # Dictionary: { base_name: [(original_file, extension), ...] }
    groups = defaultdict(list)
    for filename in all_files:
        old_path = os.path.join(folder_path, filename)
        if os.path.isfile(old_path):
            base_name, ext = os.path.splitext(filename)
            groups[base_name].append((filename, ext))

    # Sort base names alphabetically
    sorted_base_names = sorted(groups.keys())

    # ---------------
    # First pass: rename everything to a unique temp name
    # so collisions won’t occur on the second pass
    # ---------------
    temp_map = {}  # Maps old_path -> temp_path

    for base_name_files in groups.values():
        for (original_filename, ext) in base_name_files:
            old_path = os.path.join(folder_path, original_filename)
            # Create a guaranteed unique name (e.g., using uuid)
            temp_filename = f"temp_{uuid.uuid4().hex}{ext}"
            temp_path = os.path.join(folder_path, temp_filename)

            os.rename(old_path, temp_path)
            temp_map[old_path] = temp_path

    # ---------------
    # Second pass: rename from the temp name to the final numbering
    # ---------------
    current_index = 1
    for base_name in sorted_base_names:
        for (original_filename, ext) in groups[base_name]:
            old_path = os.path.join(folder_path, original_filename)
            # But note: the file is now at temp_map[old_path]
            temp_path = temp_map[os.path.join(folder_path, original_filename)]

            final_filename = f"{current_index}{ext}"
            final_path = os.path.join(folder_path, final_filename)

            print(f"Renaming '{temp_path}' -> '{final_path}'")
            os.rename(temp_path, final_path)

        current_index += 1

def main():
    if len(sys.argv) < 2:
        print("Usage: python rename_files_dataset.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    rename_files_in_order(folder_path)

if __name__ == "__main__":
    main()
