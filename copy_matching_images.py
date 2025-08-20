import os
import shutil
import sys
from pathlib import Path

def copy_matching_images(source_folder, search_folder, destination_folder):
    """
    Copies images from search_folder to destination_folder if the name matches 
    any image in the source_folder.
    
    Args:
        source_folder (str): Folder with reference images (to get the names)
        search_folder (str): Folder to search for matching images
        destination_folder (str): Folder to copy found images to
    """
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.ico'}
    
    # Create destination folder if it doesn't exist
    Path(destination_folder).mkdir(parents=True, exist_ok=True)
    
    # Get image names from source folder (without extension)
    source_names = set()
    
    print(f"Checking source folder: {source_folder}")
    if not os.path.exists(source_folder):
        print(f"Error: Source folder '{source_folder}' does not exist!")
        return False
    
    for filename in os.listdir(source_folder):
        filepath = os.path.join(source_folder, filename)
        if os.path.isfile(filepath):
            name, extension = os.path.splitext(filename)
            if extension.lower() in image_extensions:
                source_names.add(name)
    
    print(f"Found {len(source_names)} image names in source folder")
    
    # Search and copy matching files
    print(f"Searching for matching files in: {search_folder}")
    if not os.path.exists(search_folder):
        print(f"Error: Search folder '{search_folder}' does not exist!")
        return False
    
    files_copied = 0
    
    for filename in os.listdir(search_folder):
        source_path = os.path.join(search_folder, filename)
        if os.path.isfile(source_path):
            name, extension = os.path.splitext(filename)
            
            # Check if it's an image and if the name matches
            if extension.lower() in image_extensions and name in source_names:
                destination_path = os.path.join(destination_folder, filename)
                
                try:
                    shutil.copy2(source_path, destination_path)
                    print(f"Copied: {filename}")
                    files_copied += 1
                except Exception as e:
                    print(f"Error copying {filename}: {e}")
    
    print(f"\nOperation completed! {files_copied} files copied to '{destination_folder}'")
    return True

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 4:
        print("Usage: python script.py <source_folder> <search_folder> <destination_folder>")
        print("\nExample:")
        print("python script.py /path/to/reference/images /path/to/search/folder /path/to/destination")
        print("\nDescription:")
        print("- source_folder: Folder with reference images (to get names)")
        print("- search_folder: Folder to search for matching images")
        print("- destination_folder: Folder to copy found images to")
        sys.exit(1)
    
    source_folder = sys.argv[1]
    search_folder = sys.argv[2]
    destination_folder = sys.argv[3]
    
    print("=" * 60)
    print("IMAGE MATCHING AND COPYING SCRIPT")
    print("=" * 60)
    print(f"Source folder (reference): {source_folder}")
    print(f"Search folder: {search_folder}")
    print(f"Destination folder: {destination_folder}")
    print("-" * 60)
    
    success = copy_matching_images(source_folder, search_folder, destination_folder)
    
    if success:
        print("\nScript executed successfully!")
    else:
        print("\nScript execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
