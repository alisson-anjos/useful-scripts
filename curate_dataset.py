import os
import csv
import json
import shutil
import logging
import argparse
from PIL import Image
from tqdm import tqdm
from ollama import Client
from pydantic import BaseModel, ValidationError
from multiprocessing import Pool, Lock, Manager

# ========== LOG SETUP ==========
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# ========== Pydantic Schema ==========
class ImageAnalysis(BaseModel):
    quality: str
    style: str
    category: str
    descriptive_caption: str
    booru_tags: str
    resolution: str | None = None
    blur_level: str | None = None
    watermark: bool | None = None

# Shared lock for writing to CSV
global_csv_lock = Lock()

# ========== FUNCOES ==========
def ask_ollama_structured(image_path, prompt, model, host):
    client = Client(host=host, timeout=300)
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    schema = ImageAnalysis.model_json_schema()

    response = client.generate(
        model=model,
        prompt=prompt,
        images=[image_bytes],
        format=schema,
        options={'temperature': 0.2}
    )

    content = response['response']
    return ImageAnalysis.model_validate_json(content)

def ask_gemini(client, image_path, prompt):
    with open(image_path, "rb") as f:
        image_bytes = f.read()
    response = client.generate_content(
        model="gemini-pro-vision",
        contents=[
            {"role": "user", "parts": [
                {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}},
                {"text": prompt}
            ]},
        ],
    )
    return response.text.strip()

def organize_image(image_path, base_out, quality, style, category, resolution, blur_level, watermark):
    parts = [quality, blur_level or "clear", resolution or "std", "watermarked" if watermark else "clean", style, category]
    dest_dir = os.path.join(base_out, *map(str.lower, parts))
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(image_path, os.path.join(dest_dir, os.path.basename(image_path)))
    txt_src = os.path.splitext(image_path)[0] + ".txt"
    if os.path.exists(txt_src):
        shutil.copy(txt_src, os.path.join(dest_dir, os.path.basename(txt_src)))

def load_tags(txt_path):
    return open(txt_path, "r", encoding="utf-8").read().strip() if os.path.exists(txt_path) else ""

def append_csv_row(csv_path, data_dict, fieldnames):
    with global_csv_lock:
        file_exists = os.path.isfile(csv_path)
        with open(csv_path, "a", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(data_dict)

def process_single_image(args_tuple):
    filename, args, prompt_template, fieldnames, hosts, host_index = args_tuple

    if not filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
        return

    img_path = os.path.join(args.input_dir, filename)
    tags_path = os.path.splitext(img_path)[0] + ".txt"
    original_tags = load_tags(tags_path)
    host = hosts[host_index % len(hosts)]

    try:
        if args.backend == "ollama":
            data = ask_ollama_structured(img_path, prompt_template, args.model, host)
        elif args.backend == "gemini":
            from google import genai
            client = genai.Client(api_key=args.api_key)
            response_text = ask_gemini(client, img_path, prompt_template)
            data = ImageAnalysis.model_validate_json(response_text)
        else:
            raise ValueError("Invalid backend. Use 'ollama' or 'gemini'.")

        quality = data.quality.lower()
        style = data.style.lower()
        category = data.category.lower()
        resolution = (data.resolution or "std").lower()
        blur_level = (data.blur_level or "clear").lower()
        watermark = data.watermark

        organize_image(img_path, args.output_dir, quality, style, category, resolution, blur_level, watermark)

        row = {
            "filename": filename,
            "original_tags": original_tags,
            "predicted_tags": data.booru_tags,
            "descriptive_caption": data.descriptive_caption,
            "quality": quality,
            "style": style,
            "category": category,
            "resolution": resolution,
            "blur_level": blur_level,
            "watermark": watermark
        }

        append_csv_row(os.path.join(args.output_dir, "dataset_summary.csv"), row, fieldnames)
        logging.info(f"✅ {filename} -> {quality}/{blur_level}/{resolution}/{'watermarked' if watermark else 'clean'}/{style}/{category}")

    except Exception as e:
        logging.error(f"[ERROR] {filename}: {e}")

# ========== CLI ==========
def main():
    parser = argparse.ArgumentParser(description="Image dataset curation and tagging")
    parser.add_argument("--input_dir", required=True, help="Folder containing images and .txt booru tags")
    parser.add_argument("--output_dir", required=True, help="Base output folder to save organized images")
    parser.add_argument("--backend", choices=["ollama", "gemini"], default="ollama", help="Choose backend: ollama or gemini")
    parser.add_argument("--model", default="qwen:vl", help="Ollama model name (ignored if backend=gemini)")
    parser.add_argument("--api_key", help="API key for Gemini (only needed if using --backend gemini)")
    parser.add_argument("--trigger_word", default="live wallpaper", help="Word to insert if image is suitable for animation")
    parser.add_argument("--num_workers", type=int, default=4, help="Number of parallel workers to use")
    parser.add_argument("--ollama_hosts", default="http://localhost:11434", help="Comma-separated list of Ollama host URLs")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    prompt_template = (
        f"""Analyze this image and return a JSON with the following fields:
- quality: high, medium, or low
- style: anime, realistic, 3D, pixelart, etc.
- category: character, landscape, object, abstract, nsfw, etc.
- descriptive_caption: one detailed sentence
- booru_tags: list of comma-separated tags
- resolution: low, standard, or high
- blur_level: blurry, slight blur, or clear
- watermark: true or false
Add the word '{args.trigger_word}' as a tag if the image is suitable for animated live wallpapers.
"""
    )

    fieldnames = ["filename", "original_tags", "predicted_tags", "descriptive_caption", "quality", "style", "category", "resolution", "blur_level", "watermark"]

    filenames = sorted([f for f in os.listdir(args.input_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])
    hosts = [h.strip() for h in args.ollama_hosts.split(",")]

    tasks = [(fname, args, prompt_template, fieldnames, hosts, i) for i, fname in enumerate(filenames)]

    with Pool(processes=args.num_workers) as pool:
        list(tqdm(pool.imap_unordered(process_single_image, tasks), total=len(tasks), desc="Processing images"))

if __name__ == "__main__":
    main()
