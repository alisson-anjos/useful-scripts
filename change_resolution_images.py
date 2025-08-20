import os
import glob
from PIL import Image
import argparse

IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']

def resize_image_keep_aspect(image_path, output_path, base_size):
    with Image.open(image_path) as img:
        width, height = img.size
        if max(width, height) <= base_size:
            # Já está menor ou igual ao base, não precisa redimensionar
            if output_path != image_path:
                img.save(output_path)
            return

        # Determinar novo tamanho proporcional
        if width >= height:
            new_width = base_size
            new_height = int((height / width) * base_size)
        else:
            new_height = base_size
            new_width = int((width / height) * base_size)

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        resized_img.save(output_path)

def process_folder(input_dir, output_dir, base_size):
    os.makedirs(output_dir, exist_ok=True)

    image_files = []
    for ext in IMAGE_EXTENSIONS:
        image_files.extend(glob.glob(os.path.join(input_dir, f"**/*{ext}"), recursive=True))

    print(f"🔍 Found {len(image_files)} images to process.")
    
    for image_path in image_files:
        rel_path = os.path.relpath(image_path, input_dir)
        output_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        resize_image_keep_aspect(image_path, output_path, base_size)

    print(f"✅ All images resized and saved to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Downscale images proportionally to base resolution.")
    parser.add_argument("--input", required=True, help="Input folder with images")
    parser.add_argument("--output", required=True, help="Output folder (can be same as input to overwrite)")
    parser.add_argument("--base", type=int, default=1024, help="Base resolution (e.g., 1024)")

    args = parser.parse_args()
    process_folder(args.input, args.output, args.base)

if __name__ == "__main__":
    main()
