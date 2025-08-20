import argparse
import os
import glob
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from google import genai
from google.genai import types

IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_CHAR_LEN = 2048

def sanitize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('|', ' ').replace('\n', ' ')).strip()

DEFAULT_PROMPT_TEMPLATE = """
Describe the image file '{image_filename}' using a vivid and precise sentence in natural English.

Start the sentence with the trigger word: `{trigger_word}`

You are creating a caption for training a text-to-image generative model (like SDXL or Flux). The goal is to represent what is visually present using rich language and natural phrasing.

✅ Focus on:
- Main subject (e.g., a warrior in armor, a futuristic city skyline)
- Appearance and style (e.g., flowing cloak, neon-lit buildings, detailed armor)
- Scene and background (e.g., forest at dawn, cyberpunk alley, volcanic wasteland)
- Mood and color (e.g., dark and moody, ethereal glow, bright and cheerful)

⚠️ Do NOT use lists, commas, or bullet points  
⚠️ Do NOT invent unseen details  
⚠️ Write only one sentence, max 30 words, starting with `{trigger_word}`
"""

def upload_and_wait_until_active(client, path, retries=3):
    for attempt in range(retries):
        try:
            uploaded = client.files.upload(file=path)
            for _ in range(180):  # ~90s max
                status = client.files.get(name=uploaded.name)
                if str(status.state).lower() == "active":
                    return uploaded
                time.sleep(0.5)
            print(f"⏳ Timeout waiting for file activation: {path} (attempt {attempt+1})")
        except Exception as e:
            print(f"⚠️ Upload error for {path} (attempt {attempt+1}): {e}")
        time.sleep(1)
    raise RuntimeError(f"❌ Failed to activate file after {retries} attempts: {path}")

def generate_caption(image_path, args, image_filename):
    client = genai.Client(api_key=args.gemini_token)
    prompt = args.template.format(image_filename=image_filename, trigger_word=args.trigger_word)

    file = upload_and_wait_until_active(client, image_path)

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=prompt),
                types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type)
            ]
        )
    ]

    config = types.GenerateContentConfig(response_mime_type="text/plain")

    try:
        response = client.models.generate_content(
            model=args.gemini_model,
            contents=contents,
            config=config
        )

        if hasattr(response, "text") and response.text:
            caption = response.text.strip()
        elif response.parts:
            caption = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
        else:
            caption = ""

    finally:
        try:
            client.files.delete(name=file.name)
        except Exception as e:
            print(f"⚠️ Failed to delete file: {e}")

    if not caption or not caption.lower().startswith(args.trigger_word.lower()):
        return f"{args.trigger_word}, error_invalid_caption_for_{sanitize(image_filename)}"
    return caption[:MAX_CHAR_LEN]

def process_image(image_path, args):
    filename = os.path.basename(image_path)
    base_name = os.path.splitext(filename)[0]
    txt_path = os.path.join(args.output_dir_txt, base_name + ".txt")

    if args.skip_existing and os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            return base_name, f.read().strip()

    caption = generate_caption(image_path, args, filename)

    if args.save_txt:
        os.makedirs(args.output_dir_txt, exist_ok=True)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(caption)
    return base_name, caption

def main():
    parser = argparse.ArgumentParser(description="Generate image captions using Gemini Developer API")
    parser.add_argument('--folder', required=True, help='Folder with images')
    parser.add_argument('--output_dir_txt', default='captions_txt', help='Where to save .txt caption files')
    parser.add_argument('--csv_path', default='captions.csv', help='CSV output path')
    parser.add_argument('--append_csv', action='store_true', help='Append to CSV instead of overwriting')
    parser.add_argument('--skip_existing', action='store_true', help='Skip if .txt file already exists')
    parser.add_argument('--gemini_token', required=True, help='Google Gemini API Key')
    parser.add_argument('--gemini_model', default='models/gemini-pro-vision', help='Gemini model ID')
    parser.add_argument('--trigger_word', default='fluxpx', help='Trigger word prefix')
    parser.add_argument('--save_txt', action='store_true', help='Save individual .txt files')
    parser.add_argument('--num_threads', type=int, default=min(4, os.cpu_count()), help='Thread count')
    parser.add_argument('--caption_template_file', help='Custom template file (must include {image_filename} and {trigger_word})')
    args = parser.parse_args()

    if args.caption_template_file and os.path.exists(args.caption_template_file):
        with open(args.caption_template_file, 'r', encoding='utf-8') as f:
            args.template = f.read()
    else:
        args.template = DEFAULT_PROMPT_TEMPLATE

    image_paths = sorted([
        f for ext in IMAGE_EXTENSIONS
        for f in glob.glob(os.path.join(args.folder, f"**/*{ext}"), recursive=True)
    ])

    if not args.append_csv or not os.path.exists(args.csv_path):
        with open(args.csv_path, 'w', encoding='utf-8') as f:
            f.write('file_name|caption\n')

    with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
        futures = {executor.submit(process_image, path, args): path for path in image_paths}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating Captions"):
            path = futures[future]
            try:
                base_name, caption = future.result()
                with open(args.csv_path, 'a', encoding='utf-8') as f:
                    f.write(f"{sanitize(base_name)}|{sanitize(caption)}\n")
            except Exception as e:
                print(f"❌ Error processing {path}: {e}")
                fallback = f"{args.trigger_word}, error_exception"
                with open(args.csv_path, 'a', encoding='utf-8') as f:
                    f.write(f"{sanitize(os.path.splitext(os.path.basename(path))[0])}|{fallback}\n")

if __name__ == "__main__":
    main()
