# B4T-Crawler consiste em um web crawler simples e rápido, projetado para mapear rapidamente um site alvo.
# Desenvolvido por Lucas Medice (The_B4TM4N)

import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import os

# Trava para sincronizar o acesso a visitados e fila
lock = threading.Lock()

def coletar_links(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
    except:
        return set()

    soup = BeautifulSoup(response.text, "lxml")
    links = set()

    for tag in soup.find_all("a", href=True):
        link = urljoin(url, tag["href"])
        if link.startswith("http"):
            links.add(link)

    return links

def worker(dominio, max_profundidade, fila, visitados):
    while True:
        with lock:
            if not fila:
                return
            url_atual, nivel = fila.popleft()
            if url_atual in visitados:
                continue
            visitados.add(url_atual)

        if nivel < max_profundidade:
            links = coletar_links(url_atual)
            with lock:
                for link in links:
                    if urlparse(link).netloc == dominio and link not in visitados:
                        fila.append((link, nivel + 1))

def crawler_threaded(inicial, max_profundidade=3, num_threads=20):
    dominio = urlparse(inicial).netloc
    visitados = set()
    fila = deque()
    fila.append((inicial, 0))

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(dominio, max_profundidade, fila, visitados))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    return visitados

if __name__ == "__main__":
    alvo = input("Digite o alvo (ex: example.com): ").strip()
    if not alvo.startswith(("http://", "https://")):
        alvo = "https://" + alvo

    max_nivel = 3  # Profundidade fixa para velocidade
    num_threads = 20  # Threads fixas para máxima velocidade

    print(f"Iniciando B4T-Crawler...")
    print(f"Alvo: {alvo}")
    print(f"Threads: {num_threads}, Profundidade: {max_nivel}")

    start_time = time.time()

    paginas = crawler_threaded(alvo, max_profundidade=max_nivel, num_threads=num_threads)

    end_time = time.time()
    duracao = end_time - start_time

    # Salvar resultados
    timestamp = int(time.time())
    filename = f"resultados_{urlparse(alvo).netloc}_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        for pagina in sorted(paginas):
            f.write(pagina + '\n')

    print(f"\nConcluído! {len(paginas)} páginas em {duracao:.2f} segundos")
    print(f"Resultados salvos em: {filename}")