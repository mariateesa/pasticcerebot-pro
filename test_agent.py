"""
Test del modulo agent di PasticcereBot.
Testa la logica interna (memoria, preparazione messaggi) senza chiamare Groq.
Esegui con: python -m pytest test_agent.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from agent import reset_memoria, _prepara_messaggi, _salva_risposta, _storico, SYSTEM_PROMPT


# Chat ID fittizi usati solo nei test — non collideranno mai con utenti reali
CHAT_A = 99001
CHAT_B = 99002


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _pulisci(*chat_ids):
    """Rimuove gli ID di test dallo storico globale."""
    for cid in chat_ids:
        _storico.pop(cid, None)


# ---------------------------------------------------------------------------
# reset_memoria
# ---------------------------------------------------------------------------

def test_reset_memoria_azzera_storico():
    """reset_memoria deve svuotare la storia di quel chat_id."""
    _storico[CHAT_A] = [{"role": "user", "content": "ciao"}]
    reset_memoria(CHAT_A)
    assert _storico[CHAT_A] == []
    _pulisci(CHAT_A)


def test_reset_memoria_chat_mai_usato():
    """reset_memoria su un chat_id nuovo non deve sollevare eccezioni."""
    _pulisci(CHAT_B)
    reset_memoria(CHAT_B)
    assert _storico[CHAT_B] == []
    _pulisci(CHAT_B)


def test_reset_memoria_isola_chat():
    """Il reset di un chat non deve toccare la storia di un altro."""
    _storico[CHAT_A] = [{"role": "user", "content": "test a"}]
    _storico[CHAT_B] = [{"role": "user", "content": "test b"}]
    reset_memoria(CHAT_A)
    assert _storico[CHAT_A] == []
    assert _storico[CHAT_B] == [{"role": "user", "content": "test b"}]
    _pulisci(CHAT_A, CHAT_B)


# ---------------------------------------------------------------------------
# _salva_risposta
# ---------------------------------------------------------------------------

def test_salva_risposta_aggiunge_assistant():
    """_salva_risposta deve aggiungere un messaggio con role='assistant'."""
    reset_memoria(CHAT_A)
    _storico[CHAT_A].append({"role": "user", "content": "domanda"})
    _salva_risposta(CHAT_A, "Risposta di prova")
    ultimo = _storico[CHAT_A][-1]
    assert ultimo["role"] == "assistant"
    assert ultimo["content"] == "Risposta di prova"
    _pulisci(CHAT_A)


def test_salva_risposta_chat_senza_storico():
    """_salva_risposta su chat_id non inizializzato non deve crashare."""
    _pulisci(CHAT_B)
    # non deve sollevare eccezioni
    _salva_risposta(CHAT_B, "messaggio orfano")
    _pulisci(CHAT_B)


def test_salva_risposta_accoda_messaggi():
    """Più risposte devono accumularsi nell'ordine corretto."""
    reset_memoria(CHAT_A)
    _storico[CHAT_A].append({"role": "user", "content": "d1"})
    _salva_risposta(CHAT_A, "r1")
    _storico[CHAT_A].append({"role": "user", "content": "d2"})
    _salva_risposta(CHAT_A, "r2")
    assistant_msgs = [m["content"] for m in _storico[CHAT_A] if m["role"] == "assistant"]
    assert assistant_msgs == ["r1", "r2"]
    _pulisci(CHAT_A)


# ---------------------------------------------------------------------------
# _prepara_messaggi
# ---------------------------------------------------------------------------

def test_prepara_messaggi_primo_e_system_prompt():
    """Il primo elemento della lista deve essere sempre il system prompt."""
    reset_memoria(CHAT_A)
    messaggi = _prepara_messaggi("Come si fa la panna cotta?", CHAT_A)
    assert messaggi[0]["role"] == "system"
    assert messaggi[0]["content"] == SYSTEM_PROMPT
    _pulisci(CHAT_A)


def test_prepara_messaggi_contiene_domanda():
    """La domanda dell'utente deve comparire nei messaggi."""
    reset_memoria(CHAT_A)
    domanda = "Ingredienti del tiramisu?"
    messaggi = _prepara_messaggi(domanda, CHAT_A)
    testi_utente = [m["content"] for m in messaggi if m["role"] == "user"]
    assert any(domanda in t for t in testi_utente)
    _pulisci(CHAT_A)


def test_prepara_messaggi_rag_ricetta_conosciuta():
    """Per una ricetta nel dataset il contesto RAG deve essere iniettato."""
    reset_memoria(CHAT_A)
    messaggi = _prepara_messaggi("Come si fa la panna cotta?", CHAT_A)
    testi_utente = [m["content"] for m in messaggi if m["role"] == "user"]
    assert any("PANNA COTTA" in t.upper() for t in testi_utente)
    _pulisci(CHAT_A)


def test_prepara_messaggi_aggiorna_storico():
    """Dopo la chiamata, la domanda deve essere salvata nello storico."""
    reset_memoria(CHAT_A)
    domanda = "Cos'è il tiramisù?"
    _prepara_messaggi(domanda, CHAT_A)
    storico_utente = [m["content"] for m in _storico[CHAT_A] if m["role"] == "user"]
    assert domanda in storico_utente
    _pulisci(CHAT_A)


def test_prepara_messaggi_include_storia_precedente():
    """I messaggi di turni precedenti devono comparire nella lista."""
    reset_memoria(CHAT_A)
    _prepara_messaggi("Come si fa la panna cotta?", CHAT_A)
    _salva_risposta(CHAT_A, "La panna cotta si prepara con panna fresca...")
    messaggi = _prepara_messaggi("E quanta gelatina serve?", CHAT_A)
    ruoli = [m["role"] for m in messaggi]
    assert "assistant" in ruoli
    _pulisci(CHAT_A)


def test_prepara_messaggi_restituisce_lista():
    """_prepara_messaggi deve sempre restituire una lista non vuota."""
    reset_memoria(CHAT_A)
    messaggi = _prepara_messaggi("xyzxyz", CHAT_A)
    assert isinstance(messaggi, list)
    assert len(messaggi) > 0
    _pulisci(CHAT_A)
