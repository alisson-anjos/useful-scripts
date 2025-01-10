import cv2
import numpy as np
import argparse
import os
from typing import List, Tuple

def generate_video_mosaic(video_path: str, 
                           mosaic_rows: int = 4, 
                           mosaic_cols: int = 4, 
                           sample_interval: int = 10) -> np.ndarray:
    """
    Generate a mosaic image from a video file.
    
    Args:
        video_path (str): Path to the video file
        mosaic_rows (int): Number of rows in the mosaic
        mosaic_cols (int): Number of columns in the mosaic
        sample_interval (int): Frame sampling interval
    
    Returns:
        np.ndarray: Generated mosaic image
    """
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Check if video was opened correctly
    if not cap.isOpened():
        raise ValueError(f"Unable to open video file: {video_path}")
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Calculate frames to be sampled
    sampled_frames: List[np.ndarray] = []
    for frame_idx in range(0, total_frames, sample_interval):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if not ret:
            break
        
        # Resize frame to uniform size
        resized_frame = cv2.resize(frame, (width // mosaic_cols, height // mosaic_rows))
        sampled_frames.append(resized_frame)
        
        # Stop if collected enough frames for mosaic
        if len(sampled_frames) >= (mosaic_rows * mosaic_cols):
            break
    
    cap.release()
    
    # If not enough frames, repeat the last frame
    while len(sampled_frames) < (mosaic_rows * mosaic_cols):
        sampled_frames.append(sampled_frames[-1])
    
    # Reorganize frames into a mosaic
    mosaic_rows_list: List[np.ndarray] = []
    for i in range(mosaic_rows):
        row_frames = sampled_frames[i*mosaic_cols:(i+1)*mosaic_cols]
        mosaic_row = np.concatenate(row_frames, axis=1)
        mosaic_rows_list.append(mosaic_row)
    
    # Combine rows vertically
    mosaic_image = np.concatenate(mosaic_rows_list, axis=0)
    
    return mosaic_image

def save_mosaic(mosaic: np.ndarray, output_path: str) -> None:
    """
    Save the mosaic image to a file.
    
    Args:
        mosaic (np.ndarray): Mosaic image to be saved
        output_path (str): Output file path
    """
    cv2.imwrite(output_path, mosaic)

def process_video_folder(input_folder: str, 
                         output_folder: str, 
                         mosaic_rows: int = 4, 
                         mosaic_cols: int = 4, 
                         sample_interval: int = 10,
                         video_extensions: List[str] = ['.mp4', '.avi', '.mov', '.mkv']) -> List[str]:
    """
    Process all videos in a given folder and generate mosaics.
    
    Args:
        input_folder (str): Path to the folder containing videos
        output_folder (str): Path to the folder to save mosaic images
        mosaic_rows (int): Number of rows in the mosaic
        mosaic_cols (int): Number of columns in the mosaic
        sample_interval (int): Frame sampling interval
        video_extensions (List[str]): List of video file extensions to process
    
    Returns:
        List[str]: List of generated mosaic image paths
    """
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    # List to store generated mosaic paths
    generated_mosaics: List[str] = []
    
    # Iterate through all files in the input folder
    for filename in os.listdir(input_folder):
        # Check if file has a video extension
        if any(filename.lower().endswith(ext) for ext in video_extensions):
            video_path = os.path.join(input_folder, filename)
            
            try:
                # Generate mosaic
                mosaic = generate_video_mosaic(
                    video_path, 
                    mosaic_rows=mosaic_rows, 
                    mosaic_cols=mosaic_cols, 
                    sample_interval=sample_interval
                )
                
                # Create output filename
                base_filename = os.path.splitext(filename)[0]
                output_filename = f"{base_filename}_mosaic.jpg"
                output_path = os.path.join(output_folder, output_filename)
                
                # Save mosaic
                save_mosaic(mosaic, output_path)
                generated_mosaics.append(output_path)
                
                print(f"Mosaic generated for: {filename}")
            
            except Exception as e:
                print(f"Error processing {filename}: {e}")
    
    return generated_mosaics

def main():
    # Configure argument parser
    parser = argparse.ArgumentParser(description='Generate mosaics for all videos in a folder')
    parser.add_argument('input', help='Path to input folder containing videos')
    parser.add_argument('-o', '--output', 
                        default='mosaics', 
                        help='Output folder for mosaic images (default: mosaics)')
    parser.add_argument('-r', '--rows', 
                        type=int, 
                        default=4, 
                        help='Number of rows in the mosaic (default: 4)')
    parser.add_argument('-c', '--cols', 
                        type=int, 
                        default=4, 
                        help='Number of columns in the mosaic (default: 4)')
    parser.add_argument('-i', '--interval', 
                        type=int, 
                        default=10, 
                        help='Frame sampling interval (default: 10)')
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Process all videos in the input folder
        generated_mosaics = process_video_folder(
            args.input, 
            args.output, 
            mosaic_rows=args.rows, 
            mosaic_cols=args.cols, 
            sample_interval=args.interval
        )
        
        print(f"\nGenerated {len(generated_mosaics)} mosaic images in {args.output}")
    
    except Exception as e:
        print(f"Error processing video folder: {e}")

if __name__ == "__main__":
    main()