"""
Test del sistema RAG di PasticcereBot.
Esegui con: python -m pytest test_rag.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from rag import carica_ricette, cerca, _tf, _coseno


# --- Fixtures ---

@pytest.fixture
def chunks():
    return carica_ricette()


# --- Test caricamento ricette ---

def test_carica_ricette_non_vuoto(chunks):
    """Verifica che i file vengano caricati."""
    assert len(chunks) > 0

def test_carica_ricette_struttura(chunks):
    """Ogni chunk deve avere 'file' e 'testo'."""
    for chunk in chunks:
        assert "file" in chunk
        assert "testo" in chunk
        assert chunk["file"].endswith(".txt")
        assert len(chunk["testo"]) > 0

def test_carica_ricette_contiene_panna_cotta(chunks):
    """Il file panna_cotta.txt deve essere caricato."""
    files = [c["file"] for c in chunks]
    assert "panna_cotta.txt" in files

def test_carica_ricette_contiene_tiramisu(chunks):
    """Il file tiramisu.txt deve essere caricato."""
    files = [c["file"] for c in chunks]
    assert "tiramisu.txt" in files


# --- Test similarità coseno ---

def test_coseno_identico():
    """Due testi identici devono avere similarità 1.0."""
    tf = _tf("panna cotta vaniglia")
    assert abs(_coseno(tf, tf) - 1.0) < 0.001

def test_coseno_senza_parole_comuni():
    """Testi senza parole in comune devono avere similarità 0."""
    tf_a = _tf("panna cotta")
    tf_b = _tf("cioccolato fondente")
    assert _coseno(tf_a, tf_b) == 0.0

def test_coseno_range():
    """La similarità deve essere sempre tra 0 e 1."""
    tf_a = _tf("ricetta panna cotta gelatina vaniglia")
    tf_b = _tf("panna fresca zucchero latte ingredienti")
    score = _coseno(tf_a, tf_b)
    assert 0.0 <= score <= 1.0


# --- Test ricerca ---

def test_cerca_trova_per_nome(chunks):
    """Cercando 'tiramisu' deve trovare tiramisu.txt."""
    risultati = cerca("tiramisu", chunks)
    assert len(risultati) > 0
    assert any("tiramisu" in r["file"] for r in risultati)

def test_cerca_trova_panna_cotta(chunks):
    """Cercando 'panna cotta' deve trovare panna_cotta.txt."""
    risultati = cerca("panna cotta", chunks)
    assert len(risultati) > 0
    assert any("panna_cotta" in r["file"] for r in risultati)

def test_cerca_trova_per_ingrediente(chunks):
    """Cercando 'mascarpone savoiardi' deve trovare tiramisu."""
    risultati = cerca("mascarpone savoiardi", chunks)
    assert len(risultati) > 0

def test_cerca_risultati_vuoti_per_query_senza_senso(chunks):
    """Una query completamente fuori contesto non deve trovare nulla."""
    risultati = cerca("automobile motore benzina", chunks)
    assert len(risultati) == 0

def test_cerca_max_top_k(chunks):
    """I risultati non devono superare TOP_K."""
    from config import TOP_K
    risultati = cerca("uova zucchero farina burro", chunks)
    assert len(risultati) <= TOP_K
