import os
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL
from rag import carica_ricette, cerca

client = Groq(api_key=GROQ_API_KEY)

_storico: dict[int, list[dict]] = {}
MAX_MESSAGGI = 10

SYSTEM_PROMPT = """Sei PasticcereBot, un assistente esperto di pasticceria.
Rispondi sempre in italiano, con un tono cordiale e preciso.
Usa SOLO le informazioni fornite nel contesto per rispondere alle domande sulle ricette.
Se la risposta non è nel contesto, rispondi esattamente: "Non ho questa ricetta nel mio archivio." e non aggiungere altro.
Ricorda il contesto della conversazione: se l'utente dice "e quella al cioccolato?" si riferisce all'argomento precedente."""


def reset_memoria(chat_id: int) -> None:
    _storico[chat_id] = []


def _prepara_messaggi(domanda: str, chat_id: int) -> list[dict]:
    chunks = carica_ricette()
    contesto = cerca(domanda, chunks)

    if not contesto and chat_id in _storico:
        messaggi_precedenti = [
            m["content"] for m in _storico[chat_id] if m["role"] == "user"
        ][-3:]
        query_estesa = " ".join(messaggi_precedenti + [domanda])
        contesto = cerca(query_estesa, chunks)

    if contesto:
        testo_contesto = "\n\n---\n\n".join(
            f"[Ricetta: {os.path.splitext(c['file'])[0].replace('_', ' ').upper()}]\n{c['testo']}"
            for c in contesto
        )
        messaggio_utente = (
            f"Rispondi usando SOLO le informazioni qui sotto.\n\n"
            f"{testo_contesto}\n\n"
            f"Domanda dell'utente: {domanda}"
        )
    else:
        messaggio_utente = domanda

    if chat_id not in _storico:
        _storico[chat_id] = []

    storico = _storico[chat_id]
    storico_con_contesto = storico + [{"role": "user", "content": messaggio_utente}]

    if len(storico_con_contesto) > MAX_MESSAGGI * 2:
        storico_con_contesto = storico_con_contesto[-(MAX_MESSAGGI * 2):]

    storico.append({"role": "user", "content": domanda})
    if len(storico) > MAX_MESSAGGI * 2:
        _storico[chat_id] = storico[-(MAX_MESSAGGI * 2):]

    return [{"role": "system", "content": SYSTEM_PROMPT}] + storico_con_contesto


def _salva_risposta(chat_id: int, testo: str) -> None:
    if chat_id in _storico:
        _storico[chat_id].append({"role": "assistant", "content": testo})


def rispondi(domanda: str, chat_id: int) -> str:
    messaggi = _prepara_messaggi(domanda, chat_id)
    try:
        risposta = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messaggi,
        )
        testo = risposta.choices[0].message.content
    except Exception as e:
        if "api_key" in str(e).lower() or "auth" in str(e).lower():
            testo = "Chiave API Groq non valida. Controlla il file .env"
        elif "connect" in str(e).lower() or "network" in str(e).lower():
            testo = "Impossibile raggiungere Groq. Controlla la connessione internet."
        else:
            testo = f"Errore: {e}"
    _salva_risposta(chat_id, testo)
    return testo


def rispondi_stream(domanda: str, chat_id: int):
    messaggi = _prepara_messaggi(domanda, chat_id)
    testo_completo = ""
    try:
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messaggi,
            stream=True,
        )
        for chunk in stream:
            token = chunk.choices[0].delta.content or ""
            testo_completo += token
            yield token
    except Exception as e:
        if "api_key" in str(e).lower() or "auth" in str(e).lower():
            msg = "Chiave API Groq non valida. Controlla il file .env"
        elif "connect" in str(e).lower() or "network" in str(e).lower():
            msg = "Impossibile raggiungere Groq. Controlla la connessione internet."
        else:
            msg = f"Errore: {e}"
        testo_completo = msg
        yield msg
    finally:
        _salva_risposta(chat_id, testo_completo)
