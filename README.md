# PasticcereBot PRO

Bot Telegram per ricette di pasticceria, costruito da zero come progetto di studio sull'architettura degli **AI agent**.  
Niente LangChain, niente vector database: solo Python, un LLM cloud e un motore di ricerca scritto a mano.

---

## Come funziona

L'utente manda un messaggio su Telegram. Il bot:

1. **Cerca** tra 55 ricette in testo semplice quale è rilevante (sistema RAG custom)
2. **Costruisce** il prompt inserendo il testo della ricetta come contesto
3. **Chiede** a Groq (LLM gratuito su cloud) di rispondere usando solo quel contesto
4. **Streamma** la risposta token per token, aggiornando il messaggio in tempo reale

Se la ricetta non è nel dataset, risponde esattamente: *"Non ho questa ricetta nel mio archivio."*

---

## Demo

```
Utente:  Come si fa la panna cotta?
Bot:     La panna cotta si prepara con 500ml di panna fresca,
         8g di gelatina in fogli e un baccello di vaniglia.
         Scalda la panna con lo zucchero senza far bollire...

Utente:  Quanta gelatina serve esattamente?
Bot:     Per questa ricetta servono 8g di gelatina, che corrispondono
         a circa 4 fogli standard. Ammollali in acqua fredda per 10
         minuti prima di scioglierli nella panna calda.
```

---

## Comandi Telegram

| Comando | Descrizione |
|---|---|
| `/start` | Messaggio di benvenuto e lista comandi |
| `/lista` | Tutte le 55 ricette disponibili |
| `/cerca <ingrediente>` | Ricette che contengono quell'ingrediente |
| `/reset` | Cancella la memoria della chat corrente |

---

## Architettura

```
Utente (Telegram)
       │
       ▼
    bot.py          ← riceve il messaggio, gestisce lo streaming
       │
       ▼
   agent.py         ← gestisce la memoria per chat_id
       │
       ├──▶ rag.py  ← cerca nel dataset la ricetta rilevante
       │       │
       │       └──▶ data/ricette/*.txt   (55 file di testo)
       │
       └──▶ Groq API  ← genera la risposta (llama-3.1-8b-instant)
```

### Il sistema RAG (Retrieval-Augmented Generation)

Il RAG serve a "far sapere" all'LLM il contenuto delle ricette senza doverle mettere tutte nel prompt. Funziona in due fasi:

**Fase 1 — Ricerca per nome** (priorità alta)  
Se la query contiene il nome esatto di una ricetta (es. "pastiera"), viene restituito direttamente quel file.

**Fase 2 — Similarità coseno** (fallback)  
Se il nome non viene trovato, si calcola la [similarità coseno](https://en.wikipedia.org/wiki/Cosine_similarity) tra il TF della query e il TF di ogni chunk. Vengono restituiti i `TOP_K` chunk con score > 0.

**Fallback conversazionale**  
Se una domanda di follow-up non trova contesto da sola (es. *"e quella al cioccolato?"*), il sistema riprova usando gli ultimi 3 messaggi dell'utente concatenati.

---

## Stack

| Componente | Tecnologia |
|---|---|
| Linguaggio | Python 3.11+ |
| LLM | [Groq API](https://console.groq.com) — `llama-3.1-8b-instant` (gratuito) |
| Interfaccia | [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 21.x |
| RAG | Implementazione custom — nessuna dipendenza esterna |
| Hosting | [Railway](https://railway.app) (piano gratuito) |
| Test | pytest — 38 test, 0 dipendenze mock esterne |

---

## Installazione locale

### Prerequisiti

- Python 3.11 o superiore
- Token bot Telegram ([istruzioni](https://core.telegram.org/bots/tutorial))
- Chiave API Groq (gratuita su [console.groq.com](https://console.groq.com))

### Passi

```bash
# 1. Clona il repository
git clone https://github.com/mariateesa/pasticcerebot-pro.git
cd pasticcerebot-pro

# 2. Installa le dipendenze
python -m pip install -r requirements.txt

# 3. Crea il file .env
cp .env.example .env
# Apri .env e inserisci le tue chiavi

# 4. Avvia il bot
python bot.py
```

### File .env

```env
TELEGRAM_TOKEN=il_tuo_token_telegram
GROQ_API_KEY=la_tua_chiave_groq
```

---

## Test

Il progetto include 38 test automatici divisi in due file.

```bash
# Esegui tutti i test
python -m pytest test_rag.py test_agent.py -v

# Solo il motore di ricerca
python -m pytest test_rag.py -v

# Solo la logica dell'agente
python -m pytest test_agent.py -v
```

**`test_rag.py`** (27 test) — verifica il motore RAG:
- Caricamento corretto di tutti i file
- Calcolo TF e similarità coseno
- Ricerca per nome ricetta e per ingrediente
- Priorità del match per nome sul coseno
- Casi limite (query vuota, query irrilevante)

**`test_agent.py`** (11 test) — verifica la logica dell'agente senza chiamare Groq:
- Isolamento della memoria per chat_id
- Reset della conversazione
- Struttura dei messaggi inviati all'LLM
- Iniezione del contesto RAG nel prompt
- Gestione della storia multi-turno

---

## Struttura del progetto

```
pasticcerebot-pro/
├── bot.py            # Entry point — gestisce i comandi Telegram e lo streaming
├── agent.py          # Logica agente — memoria, RAG, costruzione prompt, chiamata Groq
├── rag.py            # Motore di ricerca — TF, coseno, match per nome
├── config.py         # Configurazione centralizzata (model, TOP_K, percorsi)
├── test_rag.py       # 27 test del motore RAG
├── test_agent.py     # 11 test della logica agente
├── requirements.txt
├── railway.toml      # Configurazione deploy Railway
├── .env.example
└── data/
    └── ricette/      # 55 file .txt con le ricette
        ├── tiramisu.txt
        ├── panna_cotta.txt
        ├── pastiera.txt
        └── ...
```

---

## Gestione del bot su Railway

Il bot gira su Railway 24/7 in modo automatico. Non serve fare nulla per tenerlo acceso.

### Spegnere il bot

1. Vai su [railway.app](https://railway.app) → apri il progetto
2. Clicca sul servizio del bot
3. Vai nel tab **Deployments**
4. Clicca sui tre puntini `...` accanto all'ultimo deploy attivo
5. Seleziona **Remove Deployment**

Il bot si spegne immediatamente. Le variabili d'ambiente e i file restano intatti.

### Riavviare il bot

**Opzione 1 — da Railway (senza modifiche al codice):**
1. Vai nel tab **Deployments**
2. Clicca sui tre puntini `...` accanto all'ultimo deploy
3. Seleziona **Redeploy**

**Opzione 2 — da terminale (con o senza modifiche):**
```bash
git commit --allow-empty -m "restart"
git push
```
Railway rileva il push e rideploya automaticamente.

### Aggiornare il bot

Qualsiasi `git push` sul branch `main` triggera un redeploy automatico su Railway. Non serve fare nulla di manuale.

---

## Aggiungere ricette

Crea un file `.txt` in `data/ricette/` con il nome della ricetta usando underscore al posto degli spazi (es. `creme_caramel.txt`). Il bot la rileva automaticamente al prossimo messaggio, senza riavvio.

---

## Versione locale (Ollama)

Esiste anche una versione alternativa che gira interamente offline, senza API cloud, usando [Ollama](https://ollama.com) come LLM locale:  
→ [github.com/mariateesa/pasticcerebot](https://github.com/mariateesa/pasticcerebot)
