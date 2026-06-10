"""
Test del sistema RAG di PasticcereBot.
Esegui con: python -m pytest test_rag.py -v
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from rag import carica_ricette, cerca, _tf, _coseno, _nomi_ricette_nella_query


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def chunks():
    """Carica i chunks una volta sola per tutti i test del modulo."""
    return carica_ricette()


# ---------------------------------------------------------------------------
# Caricamento ricette
# ---------------------------------------------------------------------------

def test_carica_ricette_non_vuoto(chunks):
    """Verifica che i file vengano caricati."""
    assert len(chunks) > 0


def test_carica_ricette_almeno_50(chunks):
    """Devono essere presenti almeno 50 ricette distinte."""
    files = set(c["file"] for c in chunks)
    assert len(files) >= 50


def test_carica_ricette_struttura(chunks):
    """Ogni chunk deve avere i campi 'file' e 'testo' non vuoti."""
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


def test_carica_ricette_contiene_pastiera(chunks):
    """Il file pastiera.txt deve essere caricato."""
    files = [c["file"] for c in chunks]
    assert "pastiera.txt" in files


def test_carica_ricette_nome_nel_testo(chunks):
    """Il testo di ogni chunk deve contenere il nome della ricetta (doppio prefisso)."""
    for chunk in chunks:
        nome = os.path.splitext(chunk["file"])[0].replace("_", " ")
        # il builder prepende "ricetta <nome> <nome> ..."
        assert nome in chunk["testo"].lower()


# ---------------------------------------------------------------------------
# Term Frequency (_tf)
# ---------------------------------------------------------------------------

def test_tf_somma_a_uno():
    """I valori di TF devono sommare a 1.0."""
    tf = _tf("panna cotta vaniglia zucchero")
    assert abs(sum(tf.values()) - 1.0) < 0.001


def test_tf_parole_ripetute():
    """Una parola ripetuta deve avere frequenza proporzionale."""
    tf = _tf("cioccolato cioccolato fondente")
    assert tf["cioccolato"] > tf["fondente"]


def test_tf_testo_vuoto():
    """_tf su stringa vuota non deve sollevare eccezioni."""
    tf = _tf("")
    assert isinstance(tf, dict)


# ---------------------------------------------------------------------------
# Similarità coseno (_coseno)
# ---------------------------------------------------------------------------

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
    """La similarità deve essere sempre compresa tra 0 e 1."""
    tf_a = _tf("ricetta panna cotta gelatina vaniglia")
    tf_b = _tf("panna fresca zucchero latte ingredienti")
    score = _coseno(tf_a, tf_b)
    assert 0.0 <= score <= 1.0


def test_coseno_simmetrico():
    """_coseno(a, b) deve essere uguale a _coseno(b, a)."""
    tf_a = _tf("tiramisu mascarpone savoiardi uova")
    tf_b = _tf("mascarpone caffè cacao zucchero")
    assert abs(_coseno(tf_a, tf_b) - _coseno(tf_b, tf_a)) < 0.0001


# ---------------------------------------------------------------------------
# Match per nome (_nomi_ricette_nella_query)
# ---------------------------------------------------------------------------

def test_nomi_ricette_nella_query_nome_semplice(chunks):
    """Query con 'tiramisu' deve trovare tiramisu.txt."""
    risultati = _nomi_ricette_nella_query("voglio fare il tiramisu", chunks)
    assert len(risultati) > 0
    assert any("tiramisu" in r["file"] for r in risultati)


def test_nomi_ricette_nella_query_nome_composto(chunks):
    """Query con 'panna cotta' (nome composto) deve trovare panna_cotta.txt."""
    risultati = _nomi_ricette_nella_query("come si fa la panna cotta", chunks)
    assert len(risultati) > 0
    assert any("panna_cotta" in r["file"] for r in risultati)


def test_nomi_ricette_nella_query_pastiera(chunks):
    """Query con 'pastiera' deve trovare pastiera.txt."""
    risultati = _nomi_ricette_nella_query("ricetta pastiera napoletana", chunks)
    assert len(risultati) > 0
    assert any("pastiera" in r["file"] for r in risultati)


def test_nomi_ricette_nella_query_non_trovato(chunks):
    """Query senza nomi di ricette conosciute deve ritornare lista vuota."""
    risultati = _nomi_ricette_nella_query("automobile motore benzina", chunks)
    assert len(risultati) == 0


def test_nomi_ricette_nessun_duplicato(chunks):
    """Ogni ricetta deve comparire al massimo una volta nei risultati per nome."""
    risultati = _nomi_ricette_nella_query("tiramisu", chunks)
    files = [r["file"] for r in risultati]
    assert len(files) == len(set(files))


# ---------------------------------------------------------------------------
# Ricerca principale (cerca)
# ---------------------------------------------------------------------------

def test_cerca_trova_per_nome_tiramisu(chunks):
    """Cercando 'tiramisu' deve trovare tiramisu.txt."""
    risultati = cerca("tiramisu", chunks)
    assert len(risultati) > 0
    assert any("tiramisu" in r["file"] for r in risultati)


def test_cerca_trova_panna_cotta(chunks):
    """Cercando 'panna cotta' deve trovare panna_cotta.txt."""
    risultati = cerca("panna cotta", chunks)
    assert len(risultati) > 0
    assert any("panna_cotta" in r["file"] for r in risultati)


def test_cerca_nome_ha_priorita_su_coseno(chunks):
    """Se la query contiene il nome esatto di una ricetta, deve ritornare solo quella."""
    risultati = cerca("pastiera", chunks)
    assert len(risultati) >= 1
    # tutti i risultati devono essere di pastiera.txt
    assert all("pastiera" in r["file"] for r in risultati)


def test_cerca_trova_per_ingrediente(chunks):
    """Cercando 'mascarpone savoiardi' (ingredienti del tiramisu) deve trovarlo."""
    risultati = cerca("mascarpone savoiardi", chunks)
    assert len(risultati) > 0


def test_cerca_risultati_vuoti_per_query_fuori_contesto(chunks):
    """Una query completamente irrilevante non deve restituire risultati."""
    risultati = cerca("automobile motore benzina carburatore", chunks)
    assert len(risultati) == 0


def test_cerca_max_top_k(chunks):
    """I risultati non devono mai superare TOP_K."""
    from config import TOP_K
    risultati = cerca("uova zucchero farina burro", chunks)
    assert len(risultati) <= TOP_K


def test_cerca_restituisce_lista(chunks):
    """cerca deve sempre restituire una lista (anche vuota)."""
    risultati = cerca("xyzxyzxyz", chunks)
    assert isinstance(risultati, list)
