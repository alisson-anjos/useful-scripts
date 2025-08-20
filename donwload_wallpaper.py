import os
import time
import argparse
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://alphacoders.com/",
    "Connection": "keep-alive",
}

def extrair_links_da_pagina(base_url, page):
    url = f"{base_url}?page={page}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"⚠️ Erro ao acessar a página {page}: Status {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        metas = soup.find_all("meta", itemprop="contentUrl")
        links = [m["content"] for m in metas if m.get("content", "").startswith("https://images")]
        return links
    except Exception as e:
        print(f"⚠️ Erro ao processar página {page}: {e}")
        return []

def baixar_imagem(link, caminho):
    try:
        r = requests.get(link, headers=HEADERS, timeout=15)
        with open(caminho, "wb") as f:
            f.write(r.content)
        return True
    except Exception as e:
        print(f"⚠️ Erro ao baixar {link}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="URL da categoria (ex: https://alphacoders.com/genshin-impact-wallpapers)")
    parser.add_argument("--output", default="downloads", help="Pasta onde salvar")
    parser.add_argument("--threads", type=int, default=5, help="Número de downloads simultâneos")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    page = 1
    all_links = []

    print("🔄 Iniciando varredura...")

    while True:
        print(f"🔎 Página {page}")
        links = extrair_links_da_pagina(args.url, page)
        if not links:
            print("📭 Fim das páginas ou nenhuma imagem encontrada.")
            break
        all_links.extend(links)
        page += 1
        time.sleep(1.5)  # para evitar bloqueios

    print(f"📦 Total de imagens: {len(all_links)}")

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        futures = []
        for i, url in enumerate(all_links):
            ext = url.split('.')[-1].split('?')[0]
            filename = f"img_{i+1:05d}.{ext}"
            path = os.path.join(args.output, filename)
            futures.append(executor.submit(baixar_imagem, url, path))

        for _ in tqdm(as_completed(futures), total=len(futures), desc="⬇️ Baixando"):
            pass

    print(f"✅ Finalizado. Imagens salvas em: {args.output}")

if __name__ == "__main__":
    main()
