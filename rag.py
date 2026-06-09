import os
import math
from config import RICETTE_DIR, CHUNK_SIZE, TOP_K


def carica_ricette() -> list[dict]:
    chunks = []
    for nome_file in os.listdir(RICETTE_DIR):
        if not nome_file.endswith(".txt"):
            continue
        percorso = os.path.join(RICETTE_DIR, nome_file)
        with open(percorso, encoding="utf-8") as f:
            testo = f.read()
        nome_ricetta = os.path.splitext(nome_file)[0].replace("_", " ")
        parole = testo.split()
        for i in range(0, len(parole), CHUNK_SIZE):
            chunk = " ".join(parole[i : i + CHUNK_SIZE])
            testo_con_nome = f"ricetta {nome_ricetta} {nome_ricetta} {chunk}"
            chunks.append({"file": nome_file, "testo": testo_con_nome})
    return chunks


def _tf(testo: str) -> dict[str, float]:
    parole = testo.lower().split()
    freq: dict[str, float] = {}
    for p in parole:
        freq[p] = freq.get(p, 0) + 1
    totale = len(parole) or 1
    return {p: c / totale for p, c in freq.items()}


def _coseno(a: dict, b: dict) -> float:
    comuni = set(a) & set(b)
    if not comuni:
        return 0.0
    dot = sum(a[k] * b[k] for k in comuni)
    norm_a = math.sqrt(sum(v**2 for v in a.values()))
    norm_b = math.sqrt(sum(v**2 for v in b.values()))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _nomi_ricette_nella_query(query: str, chunks: list[dict]) -> list[dict]:
    parole_query = query.lower().split()
    trovati = []
    visti = set()
    for chunk in chunks:
        nome_file = chunk["file"]
        if nome_file in visti:
            continue
        nome_ricetta = os.path.splitext(nome_file)[0].replace("_", " ").lower()
        parole_nome = nome_ricetta.split()
        if all(p in parole_query for p in parole_nome):
            trovati.append(chunk)
            visti.add(nome_file)
    return trovati


def cerca(query: str, chunks: list[dict]) -> list[dict]:
    per_nome = _nomi_ricette_nella_query(query, chunks)
    if per_nome:
        return per_nome[:TOP_K]

    tf_query = _tf(query)
    scored = [
        (chunk, _coseno(tf_query, _tf(chunk["testo"]))) for chunk in chunks
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [chunk for chunk, score in scored[:TOP_K] if score > 0]
