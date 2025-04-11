import os
import shutil
import random
import sys

def main():
    # User inputs
    source_folder = input("Enter the source folder path: ").strip()
    dest_folder = input("Enter the destination folder path: ").strip()
    try:
        num_videos = int(input("Enter the number of videos to transfer: "))
    except ValueError:
        print("Invalid number!")
        sys.exit(1)

    # Ask whether to move files instead of copying them
    move_files_input = input("Do you want to move the files instead of copying them? (y/n): ").strip().lower()
    move_files = (move_files_input == 'y')

    # Check if the folders exist
    if not os.path.isdir(source_folder):
        print(f"Source folder '{source_folder}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(dest_folder):
        print(f"Destination folder '{dest_folder}' does not exist. Creating...")
        os.makedirs(dest_folder, exist_ok=True)

    # List of video extensions to be considered
    video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.flv', '.wmv']

    # List all video files in the source folder
    video_files = [
        f for f in os.listdir(source_folder)
        if os.path.isfile(os.path.join(source_folder, f)) and os.path.splitext(f)[1].lower() in video_extensions
    ]

    if not video_files:
        print("No video files found in the source folder.")
        sys.exit(1)

    # Adjust the number of videos if the requested number is higher than available
    if num_videos > len(video_files):
        print(f"There are only {len(video_files)} videos available. All videos will be transferred.")
        num_videos = len(video_files)

    # Select N random videos
    selected_videos = random.sample(video_files, num_videos)

    # Transfer the videos and their corresponding .txt files (if they exist)
    for video in selected_videos:
        source_video_path = os.path.join(source_folder, video)
        dest_video_path = os.path.join(dest_folder, video)
        try:
            if move_files:
                shutil.move(source_video_path, dest_video_path)
                print(f"Video moved: {video}")
            else:
                shutil.copy2(source_video_path, dest_video_path)
                print(f"Video copied: {video}")
        except Exception as e:
            print(f"Error transferring {video}: {e}")
            continue

        # Check if there is a .txt file with the same name as the video
        base_name, _ = os.path.splitext(video)
        txt_file = base_name + ".txt"
        source_txt_path = os.path.join(source_folder, txt_file)
        if os.path.exists(source_txt_path):
            dest_txt_path = os.path.join(dest_folder, txt_file)
            try:
                if move_files:
                    shutil.move(source_txt_path, dest_txt_path)
                    print(f"Text file moved: {txt_file}")
                else:
                    shutil.copy2(source_txt_path, dest_txt_path)
                    print(f"Text file copied: {txt_file}")
            except Exception as e:
                print(f"Error transferring {txt_file}: {e}")

if __name__ == "__main__":
    main()
