# import argparse
# import os
# import uuid
# import warnings
# import glob
# import re
# from collections import defaultdict
# from concurrent.futures import ThreadPoolExecutor, as_completed

# import torch
# import subprocess
# from tqdm import tqdm

# from google import genai
# from google.genai import types

# warnings.filterwarnings('ignore', category=UserWarning)

# MAX_CHAR_LEN = 1000

# VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

# delete_executor = ThreadPoolExecutor(max_workers=4)

# def clean_text(text: str) -> str:
    # text = re.sub(r"<\|.*?\|>", " ", text)
    # return " ".join(text.split())

# def sanitize_csv_field(text: str) -> str:
    # return re.sub(r'\s+', ' ', text.replace('|', ' ').replace('\n', ' ').replace('\r', ' ')).strip()

# def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    # os.makedirs(output_dir, exist_ok=True)
    # output_path = os.path.join(output_dir, f"{uuid.uuid4().hex}.wav")
    # command = [
        # 'ffmpeg', '-y', '-i', video_path,
        # '-vn', '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
        # output_path
    # ]
    # subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    # return output_path

# def split_audio_fixed(audio_path: str, output_dir: str, segment_length: int = 30,
                      # trim_start: float = 0.0, trim_end: float = 0.0) -> list[str]:
    # import torchaudio
    # waveform, sr = torchaudio.load(audio_path)
    # if waveform.dim() > 1:
        # waveform = waveform.mean(dim=0, keepdim=True)
    # total = waveform.size(1)
    # start = int(trim_start * sr)
    # end = total - int(trim_end * sr)
    # waveform = waveform[:, start:end]

    # paths = []
    # seg_samples = int(segment_length * sr)
    # for i in range(0, waveform.size(1), seg_samples):
        # seg = waveform[:, i:i + seg_samples]
        # fname = f"{uuid.uuid4().hex}.wav"
        # seg_path = os.path.join(output_dir, fname)
        # torchaudio.save(seg_path, seg, sr)
        # paths.append(seg_path)
    # return paths

# def generate_caption_with_gemini(audio_path, gemini_api_key, gemini_model, video_filename, template=None):
    # client = genai.Client(api_key=gemini_api_key)
    # model = f"{gemini_model}"

    # default_prompt = (
        # f"Describe the visual style and motion of the video '{video_filename}'. "
        # "Mention camera movement (fast, slow, parallax), background dynamics, particles, hair or fluid motion, and aesthetic style. "
        # "At the end, summarize the key visual features as a list of lowercase tags separated by commas (e.g., slow_motion, parallax, particles). "
        # "Also indicate if the scene has only character, only environment, or both."
    # )
    # prompt = template if template else default_prompt

    # file = client.files.upload(file=audio_path)

    # contents = [
        # types.Content(
            # role="user",
            # parts=[
                # types.Part.from_text(text=prompt),
                # types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type)
            # ],
        # ),
    # ]

    # config = types.GenerateContentConfig(response_mime_type="text/plain")
    # try:
        # output = client.models.generate_content(
            # model=model,
            # contents=contents,
            # config=config
        # )
        # text = output.text.strip()
        # if "\n" in text:
            # parts = text.split("\n")
            # desc = parts[0].strip()
            # tags = parts[-1].strip()
        # else:
            # desc = text.strip()
            # tags = "style_unknown"
        # return desc[:MAX_CHAR_LEN], tags[:MAX_CHAR_LEN]
    # except Exception as e:
        # raise RuntimeError(f"Gemini caption generation failed: {e}")
    # finally:
        # try:
            # delete_executor.submit(client.files.delete, name=file.name)
        # except Exception as e:
            # print(f"⚠️ Failed to queue Gemini file deletion: {e}")

# def process_segment(seg_path, args, video_filename=None) -> str:
    # filename = os.path.basename(seg_path)
    # try:
        # desc, tags = generate_caption_with_gemini(
            # audio_path=seg_path,
            # gemini_api_key=args.gemini_token,
            # gemini_model=args.gemini_model,
            # video_filename=video_filename or filename,
            # template=args.caption_template
        # )
        # return f"{args.trigger_word.strip()} {desc.strip()}\n{tags.strip()}"
    # except Exception as e:
        # print(f"⚠️ Gemini failed on {filename}: {e}")
        # return ""

# def process_segments(seg_paths, args, base_name):
    # def worker(seg):
        # base = os.path.splitext(seg)[0]
        # txt_file = os.path.join(args.output_dir, base_name + ".txt")

        # if args.skip_existing and os.path.exists(txt_file):
            # return None

        # caption = process_segment(seg, args, video_filename=base_name)
        # if not caption.strip():
            # return None

        # if args.save_txt:
            # with open(txt_file, 'w', encoding='utf-8') as f:
                # f.write(caption)

        # row = [sanitize_csv_field(base_name), sanitize_csv_field(caption.replace('\n', ' '))]
        # with open(args.csv_path, 'a', encoding='utf-8') as f_csv:
            # f_csv.write('|'.join(row) + '\n')
        # return True

    # with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
        # futures = [executor.submit(worker, seg) for seg in seg_paths]
        # for _ in tqdm(as_completed(futures), total=len(futures), desc='Segments'):
            # pass

# def main():
    # parser = argparse.ArgumentParser(description="Generate live wallpaper captions from videos using Gemini")
    # parser.add_argument('--folder', required=True, help='Folder with video files')
    # parser.add_argument('--output_dir', default='segments', help='Segments output folder')
    # parser.add_argument('--csv_path', default='captions.csv', help='CSV output path')
    # parser.add_argument('--segment_length', type=int, default=5, help='Segment length in seconds')
    # parser.add_argument('--trim_start', type=float, default=0.0, help='Trim seconds from start')
    # parser.add_argument('--trim_end', type=float, default=0.0, help='Trim seconds from end')
    # parser.add_argument('--append_csv', action='store_true', help='Append to existing CSV')
    # parser.add_argument('--skip_existing', action='store_true', help='Skip existing .txt outputs')
    # parser.add_argument('--gemini_token', type=str, required=True, help='Gemini API key')
    # parser.add_argument('--num_threads', type=int, default=os.cpu_count(), help='Number of threads')
    # parser.add_argument('--gemini_model', type=str, default='models/gemini-2.5-flash-preview-04-17', help='Gemini model')
    # parser.add_argument('--caption_template', type=str, default=None, help='Custom prompt template')
    # parser.add_argument('--trigger_word', type=str, required=True, help='Trigger word prefix')
    # parser.add_argument('--save_txt', action='store_true', help='Save captions as individual .txt files')
    # args = parser.parse_args()

    # if not args.append_csv or not os.path.exists(args.csv_path):
        # with open(args.csv_path, 'w', encoding='utf-8') as f:
            # f.write('video|text\n')

    # video_files = [f for ext in VIDEO_EXTENSIONS for f in glob.glob(os.path.join(args.folder, f'*{ext}'))]

    # for video_path in video_files:
        # base_name = os.path.splitext(os.path.basename(video_path))[0]
        # print(f"\n🎬 Processing: {video_path}")
        # audio_path = extract_audio_from_video(video_path, args.output_dir)
        # segments = split_audio_fixed(
            # audio_path,
            # os.path.join(args.output_dir, base_name),
            # args.segment_length, args.trim_start, args.trim_end
        # )
        # process_segments(segments, args, base_name)

    # print(f"\n✅ Captions saved to: {args.csv_path}")

# if __name__ == '__main__':
    # main()


import argparse
import os
import warnings
import glob
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from tqdm import tqdm
from google import genai
from google.genai import types

warnings.filterwarnings('ignore', category=UserWarning, module='google.generativeai.client')
warnings.filterwarnings('ignore', category=UserWarning, module='google.ai.generativelanguage')

MAX_CHAR_LEN_TAGS = 2048
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
#Start the sentence with the trigger word: `{trigger_word}`
#⚠️ Write only one sentence, max **25 words**, starting with `{trigger_word}`
# --- INÍCIO DO PROMPT TEMPLATE ---
DEFAULT_CAPTION_TEMPLATE = """
Analyze the video file '{video_filename}' and describe it using a single, vivid sentence.

⚠️ Write only one sentence, max **40 words**

You are generating a motion-aware caption for training or inference using a live wallpaper-style LoRA.

Your sentence must describe the **visible movement**, **camera behavior**, **hair/fabric animation**, and **ambient effects** present in the scene.

✅ Focus especially on:
- **Motion style and speed** (e.g., hair flowing gently, fabric swaying, slow breathing, subtle character motion)
- **Camera behavior** (e.g., static camera, slow zoom, slight parallax)
- **Effects and particles** (e.g., glowing embers, drifting petals, magical mist, water ripples)
- **Atmosphere and tone** (e.g., dreamlike ambiance, fantasy setting, serene mood)
- **Visual composition** (e.g., backlit, warm colors, anime-style design)
- **Subject** (e.g., character, girl, man, boy... creature..)
- **Quality** (e.g., 4k, 8k, full hd, high quality, detailed... micro details)

⚠️ Do NOT use tags, commas, or bullet points  
⚠️ Do NOT invent elements — describe only what is visible  


✅ Output format:

A girl stands beneath falling petals, her long hair swaying as soft light glows through fog while the camera remains still and ambient particles drift.

"""
# --- FIM DO PROMPT TEMPLATE ---

def sanitize_csv_field(text: str) -> str:
    return re.sub(r'\s+', ' ', text.replace('|', ' ').replace('\n', ' ').replace('\r', ' ')).strip()

def generate_caption_with_gemini(
    video_path: str,
    gemini_api_key: str,
    gemini_model_name: str,
    video_filename: str,
    base_prompt_template: str,
    trigger_word: str
) -> str:
    client = genai.Client(api_key=gemini_api_key)
    model_for_api = gemini_model_name

    prompt_to_send = base_prompt_template.format(video_filename=video_filename, trigger_word=trigger_word)
    # print(f"DEBUG: Enviando prompt para {video_filename}:\n{prompt_to_send[:200]}...")

    uploaded_file_details = None
    try:
        # print(f"DEBUG: Fazendo upload de {video_path}")
        try:
            uploaded_file_details = client.files.upload(file_path=video_path)
        except TypeError:
            try:
                uploaded_file_details = client.files.upload(path=video_path)
            except TypeError:
                 uploaded_file_details = client.files.upload(file=video_path)

        # print(f"DEBUG: Upload de {video_path} como {uploaded_file_details.name}, estado inicial: {uploaded_file_details.state}")

        for i in range(120):
            current_file_status = client.files.get(name=uploaded_file_details.name)
            # print(f"DEBUG Polling {i+1}: {current_file_status.name} state: {current_file_status.state}")
            current_state_str = str(current_file_status.state).upper()
            if "ACTIVE" in current_state_str:
                break
            time.sleep(0.5)
        else:
            # print(f"DEBUG: Arquivo {uploaded_file_details.name} não ficou ativo. Último estado: {current_file_status.state}")
            raise RuntimeError(f"Arquivo {uploaded_file_details.name} não ativo após upload. Último estado: {current_file_status.state}")
        # print(f"DEBUG: Arquivo {uploaded_file_details.name} está ativo.")

        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt_to_send),
                    types.Part.from_uri(file_uri=uploaded_file_details.uri, mime_type=uploaded_file_details.mime_type)
                ],
            ),
        ]
        
        # Renomeado para config_obj para evitar confusão com o parâmetro 'config' da função
        config_obj = types.GenerateContentConfig(
            response_mime_type="text/plain",
            candidate_count=1
        )

        # print(f"DEBUG: Gerando conteúdo com o modelo {model_for_api}...")
        response = client.models.generate_content(
            model=model_for_api,
            contents=contents,
            config=config_obj # <--- CORREÇÃO APLICADA AQUI
        )
        # print("DEBUG: Resposta recebida do Gemini.")

        raw_gemini_output_text = ""
        if hasattr(response, 'text') and response.text:
            raw_gemini_output_text = response.text.strip()
        elif response.parts:
            raw_gemini_output_text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
        
        if not raw_gemini_output_text:
            # print(f"⚠️ Gemini retornou texto vazio para {video_filename}.") # Descomente para debug
            return f"{trigger_word}, error_gemini_returned_empty_text_for_{sanitize_csv_field(video_filename)}"

        lines = [line.strip() for line in raw_gemini_output_text.split('\n') if line.strip()]
        final_caption_line = lines[-1] if lines else ""

        if not final_caption_line:
            #  print(f"⚠️ Nenhuma linha de legenda válida encontrada na saída do Gemini para {video_filename}. Saída crua: '{raw_gemini_output_text}'") # Descomente para debug
             return f"{trigger_word}, error_no_valid_caption_line_for_{sanitize_csv_field(video_filename)}"

        # if not final_caption_line.lower().startswith(trigger_word.lower()): # Descomente para debug
        #    print(f"INFO: Legenda para '{video_filename}' NÃO começou com a trigger '{trigger_word}'. Saída: '{final_caption_line}'")

        return final_caption_line[:MAX_CHAR_LEN_TAGS]

    except Exception as e:
        print(f"‼️ ERRO em generate_caption_with_gemini para {video_filename}: {type(e).__name__} - {e}")
        # import traceback
        # traceback.print_exc() # Descomente para debug MUITO detalhado do erro exato
        return f"{trigger_word}, error_exception_during_generation_for_{sanitize_csv_field(video_filename)}"
    finally:
        if uploaded_file_details and hasattr(uploaded_file_details, 'name'):
            try:
                # print(f"DEBUG: Tentando excluir arquivo {uploaded_file_details.name}")
                client.files.delete(name=uploaded_file_details.name)
            except Exception as e_del:
                print(f"⚠️ Falha ao excluir arquivo Gemini {uploaded_file_details.name}: {e_del}")


def process_video_for_caption(video_path: str, args: argparse.Namespace) -> tuple[str, str]:
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    # print(f"🎬 Processando: {video_path}")

    if args.skip_existing_txt:
        txt_file_path = os.path.join(args.output_dir_txt, base_name + ".txt")
        if os.path.exists(txt_file_path):
            try:
                with open(txt_file_path, 'r', encoding='utf-8') as f_txt:
                    existing_caption = f_txt.read().strip()
                if existing_caption:
                    # print(f"⏭️ Usando .txt existente: {txt_file_path}")
                    return base_name, existing_caption
            except Exception as e_read:
                print(f"⚠️ Erro ao ler .txt {txt_file_path}: {e_read}. Gerando novamente.")

    template_to_use = args.custom_caption_template_content if args.custom_caption_template_content else DEFAULT_CAPTION_TEMPLATE
    
    caption_from_gemini = generate_caption_with_gemini(
        video_path=video_path,
        gemini_api_key=args.gemini_token,
        gemini_model_name=args.gemini_model,
        video_filename=base_name,
        base_prompt_template=template_to_use,
        trigger_word=args.trigger_word
    )

    final_caption_for_files = caption_from_gemini.strip()

    if not final_caption_for_files or \
       final_caption_for_files.lower() == args.trigger_word.lower() or \
       final_caption_for_files.lower() == args.trigger_word.lower() + ",":
        # print(f"⚠️ Legenda final vazia ou mínima para {base_name} após chamada Gemini. Saída Gemini: '{caption_from_gemini}'. Usando erro padrão.") # Descomente para debug
        final_caption_for_files = f"{args.trigger_word}, error_empty_or_minimal_output_for_{sanitize_csv_field(base_name)}"
    
    # if not final_caption_for_files.lower().startswith(args.trigger_word.lower()): # Descomente para debug
    #    print(f"INFO: Legenda para '{base_name}' NÃO começou com a trigger '{args.trigger_word}'. Legenda: '{final_caption_for_files}'")


    return base_name, final_caption_for_files


def main():
    parser = argparse.ArgumentParser(description="Gera legendas (tags) de vídeos de live wallpaper usando Gemini")
    parser.add_argument('--folder', required=True, help='Pasta com arquivos de vídeo (pode buscar recursivamente)')
    parser.add_argument('--output_dir_txt', default='captions_txt', help='Pasta de saída para arquivos .txt')
    parser.add_argument('--csv_path', default='metadata.csv', help='Caminho de saída do CSV (ex: metadata.csv)')
    parser.add_argument('--append_csv', action='store_true', help='Anexar ao CSV existente em vez de sobrescrever')
    parser.add_argument('--skip_existing_txt', action='store_true', help='Pular vídeos se um arquivo de legenda .txt já existir (lê o conteúdo se existir)')
    parser.add_argument('--gemini_token', type=str, required=True, help='Chave API do Google AI Studio para Gemini')
    parser.add_argument('--num_threads', type=int, default=min(2, os.cpu_count() or 1), help='Número de threads paralelas (reduzido para evitar rate limit).')
    parser.add_argument('--gemini_model', type=str, default='models/gemini-pro-vision', help='Modelo Gemini a ser usado (ex: models/gemini-pro-vision para API com client.files ou models/gemini-1.5-flash-latest para API mais nova)')
    parser.add_argument('--caption_template_file', type=str, default=None, help='Caminho para um arquivo de texto de template de prompt personalizado. Substitui o padrão. Deve conter os placeholders {video_filename} e {trigger_word}.')
    parser.add_argument('--trigger_word', type=str, default='lvwpx', help="Trigger word primária a ser incluída no prompt e no início da legenda.")
    parser.add_argument('--save_txt', action='store_true', help='Salvar legendas como arquivos .txt individuais em output_dir_txt')
    
    args = parser.parse_args()

    args.custom_caption_template_content = None
    if args.caption_template_file:
        try:
            with open(args.caption_template_file, 'r', encoding='utf-8') as f:
                args.custom_caption_template_content = f.read()
                if "{video_filename}" not in args.custom_caption_template_content or \
                   "{trigger_word}" not in args.custom_caption_template_content:
                    print(f"⚠️ Template personalizado de {args.caption_template_file} está faltando os placeholders obrigatórios '{{video_filename}}' ou '{{trigger_word}}'. Usando template padrão.")
                    args.custom_caption_template_content = None
                else:
                    print(f"📋 Usando template de legenda personalizado de: {args.caption_template_file}")
        except Exception as e:
            print(f"⚠️ Não foi possível carregar o template personalizado de {args.caption_template_file}: {e}. Usando template padrão.")

    if args.save_txt:
        os.makedirs(args.output_dir_txt, exist_ok=True)

    if not args.append_csv or not os.path.exists(args.csv_path):
        csv_dir = os.path.dirname(args.csv_path)
        if csv_dir and not os.path.exists(csv_dir):
            os.makedirs(csv_dir, exist_ok=True)
        with open(args.csv_path, 'w', encoding='utf-8') as f:
            f.write('file_name|caption\n')

    video_files = sorted([f for ext in VIDEO_EXTENSIONS for f in glob.glob(os.path.join(args.folder, f'**/*{ext}'), recursive=True)])
    
    if not video_files:
        print(f"Nenhum arquivo de vídeo encontrado em {args.folder} com as extensões {VIDEO_EXTENSIONS}")
        return

    print(f"Encontrados {len(video_files)} arquivos de vídeo para processar com a trigger word '{args.trigger_word}'.")
    print(f"Usando modelo Gemini: {args.gemini_model}")


    with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
        futures_map = {executor.submit(process_video_for_caption, video_path, args): video_path for video_path in video_files}
        
        for future in tqdm(as_completed(futures_map), total=len(video_files), desc="Gerando Legendas"):
            video_path_processed = futures_map[future]
            try:
                base_name, caption_tags = future.result()
                
                if args.save_txt:
                    txt_file = os.path.join(args.output_dir_txt, base_name + ".txt")
                    with open(txt_file, 'w', encoding='utf-8') as f_txt:
                        f_txt.write(caption_tags)
                
                caption_for_csv = sanitize_csv_field(caption_tags)
                row = [sanitize_csv_field(base_name), caption_for_csv]
                
                with open(args.csv_path, 'a', encoding='utf-8') as f_csv:
                    f_csv.write('|'.join(row) + '\n')

            except Exception as e:
                print(f"‼️ Erro FATAL ao processar vídeo {video_path_processed} no loop principal: {type(e).__name__} - {e}")
                # import traceback
                # traceback.print_exc()
                error_base_name = os.path.splitext(os.path.basename(video_path_processed))[0]
                error_row = [sanitize_csv_field(error_base_name), f"{args.trigger_word}, error_fatal_processing_in_main_loop"]
                with open(args.csv_path, 'a', encoding='utf-8') as f_csv:
                    f_csv.write('|'.join(error_row) + '\n')

    print(f"\n✅ Geração de legendas concluída. Saídas em '{args.output_dir_txt}' (se --save_txt) e CSV em '{args.csv_path}'")

if __name__ == '__main__':
    main()