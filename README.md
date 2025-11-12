# B4T-Crawler – Documentação Técnica

O **B4T-Crawler** é um web crawler multithreaded desenvolvido em Python, criado para realizar o mapeamento rápido de sites, coletando todos os links internos até um nível de profundidade determinado.

Este documento explica detalhadamente **como o código funciona**, descrevendo cada componente e sua função dentro do processo de varredura.

---

## 1. Visão Geral

O script realiza uma varredura (crawl) a partir de uma URL inicial, coletando e armazenando todos os links pertencentes ao mesmo domínio.  
O processo é acelerado com o uso de **threads** que trabalham em paralelo, compartilhando uma **fila de URLs** e um **conjunto de páginas visitadas**.

Fluxo resumido:
1. O usuário informa o alvo (URL).
2. O crawler inicia com parâmetros fixos (profundidade e threads).
3. As threads começam a explorar as páginas, coletando links internos.
4. Todos os links são salvos em um arquivo `.txt` ao final.

---

## 2. Estrutura do Código

O código é dividido em partes principais:

1. Importações e variáveis globais
2. Função `coletar_links(url)`
3. Função `worker()`
4. Função `crawler_threaded()`
5. Bloco principal (`if __name__ == "__main__":`)

---

## 3. Importações

```python
import threading
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time
import os
```

### Função de cada biblioteca:
- **threading**: cria e gerencia as threads responsáveis por explorar as páginas simultaneamente.  
- **requests**: realiza as requisições HTTP para obter o conteúdo HTML das páginas.  
- **BeautifulSoup (bs4)**: faz o parsing do HTML e extrai os links.  
- **urllib.parse**: manipula URLs, combinando caminhos relativos (`urljoin`) e extraindo o domínio (`urlparse`).  
- **collections.deque**: fornece uma fila eficiente para armazenar e acessar URLs pendentes.  
- **time / os**: usados para medir a duração e gerar o nome do arquivo de saída.

Também há uma variável global:

```python
lock = threading.Lock()
```

Essa **trava** garante que múltiplas threads não acessem simultaneamente estruturas compartilhadas (`fila` e `visitados`), evitando condições de corrida.

---

## 4. Função `coletar_links(url)`

```python
def coletar_links(url):
    headers = {"User-Agent": "Mozilla/5.0 ..."}
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
```

### Explicação:
- Envia uma requisição HTTP para a URL fornecida.
- Em caso de erro (timeout, 404, etc.), retorna um conjunto vazio.
- Usa o BeautifulSoup para analisar o HTML e localizar todas as tags `<a href="...">`.
- Converte links relativos em absolutos com `urljoin()`.
- Retorna apenas links que começam com “http” (ignorando ancoras e caminhos inválidos).
- O retorno é um **conjunto (`set`) de URLs únicas**.

---

## 5. Função `worker(dominio, max_profundidade, fila, visitados)`

Essa função é executada por cada thread e representa o **núcleo do trabalho**.

```python
def worker(dominio, max_profundidade, fila, visitados):
    while True:
        with lock:
            if not fila:
                return
            url_atual, nivel = fila.popleft()
            if url_atual in visitados:
                continue
            visitados.add(url_atual)
```

### Etapa 1 – Controle de fila:
- Usa o `lock` para garantir exclusividade no acesso à fila.
- Retira o próximo item (`url_atual`, `nivel`) da fila.
- Ignora se a URL já foi visitada.
- Adiciona ao conjunto `visitados`.

### Etapa 2 – Coleta de novos links:
```python
        if nivel < max_profundidade:
            links = coletar_links(url_atual)
            with lock:
                for link in links:
                    if urlparse(link).netloc == dominio and link not in visitados:
                        fila.append((link, nivel + 1))
```

- Se o nível atual for menor que o limite, a função chama `coletar_links()`.
- Para cada link encontrado:
  - Verifica se pertence ao mesmo domínio.
  - Se ainda não visitado, adiciona à fila com o nível incrementado.

Assim, as threads trabalham em paralelo até que a fila esteja vazia.

---

## 6. Função `crawler_threaded(inicial, max_profundidade=3, num_threads=20)`

Essa função **coordena todo o processo**.

```python
def crawler_threaded(inicial, max_profundidade=3, num_threads=20):
    dominio = urlparse(inicial).netloc
    visitados = set()
    fila = deque()
    fila.append((inicial, 0))
```

Inicializa:
- O domínio base.
- A fila com a URL inicial.
- O conjunto de páginas visitadas.

Cria e inicia as threads:
```python
    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker, args=(dominio, max_profundidade, fila, visitados))
        t.start()
        threads.append(t)
```

Aguarda todas terminarem:
```python
    for t in threads:
        t.join()
    return visitados
```

No fim, retorna um conjunto com **todas as páginas encontradas**.

---

## 7. Bloco principal (`__main__`)

```python
if __name__ == "__main__":
    alvo = input("Digite o alvo (ex: example.com): ").strip()
    if not alvo.startswith(("http://", "https://")):
        alvo = "https://" + alvo

    max_nivel = 3
    num_threads = 20
```

- Solicita o alvo ao usuário.
- Garante que a URL tenha protocolo válido.
- Define parâmetros padrão de profundidade e threads.

O programa então:
1. Exibe as configurações.
2. Inicia a varredura com `crawler_threaded()`.
3. Mede o tempo total de execução.
4. Salva os resultados num arquivo nomeado com base no domínio e timestamp.

---

## 8. Saída e Armazenamento

```python
filename = f"resultados_{urlparse(alvo).netloc}_{timestamp}.txt"
with open(filename, 'w', encoding='utf-8') as f:
    for pagina in sorted(paginas):
        f.write(pagina + '\n')
```

Os links coletados são armazenados de forma ordenada, um por linha.

---

## 9. Conclusão

O **B4T-Crawler** é uma ferramenta simples, mas eficiente, que demonstra bem:
- O uso de **multithreading** para tarefas I/O-bound.  
- A importância de **sincronização de dados** em ambientes concorrentes.  
- O fluxo básico de **coleta e filtragem de links** em crawlers reais.

Sua arquitetura modular facilita futuras expansões, como:
- Suporte a `robots.txt`
- Armazenamento em banco de dados
- CLI completa com `argparse`
- Exportação para JSON/CSV

---

> "Mapeie a web com inteligência, não com força bruta."  
> — The_B4TM4N
