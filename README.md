# PasticcereBot PRO

Bot Telegram con AI per ricette di pasticceria. Utilizza un sistema RAG custom per rispondere a domande su oltre 50 ricette, con memoria della conversazione e streaming della risposta in tempo reale.

## Demo

```
Utente:  Come si fa la panna cotta?
Bot:     La panna cotta si prepara con 500ml di panna fresca,
         8g di gelatina in fogli e un baccello di vaniglia...

Utente:  Quanta gelatina serve esattamente?
Bot:     Per questa ricetta servono 8g di gelatina (4 fogli)...
```

## Funzionalità

- **RAG custom** — ricerca nei file di testo per nome ricetta e similarità coseno
- **Memoria conversazione** — ricorda il contesto degli ultimi 10 scambi
- **Streaming risposta** — la risposta appare in tempo reale come ChatGPT
- **`/lista`** — tutte le ricette disponibili
- **`/cerca <ingrediente>`** — filtra ricette per ingrediente
- **`/reset`** — cancella la memoria della chat

## Stack

- **Python** — linguaggio principale
- **Groq API** — LLM cloud gratuito (llama-3.2-3b)
- **python-telegram-bot** — interfaccia Telegram
- **RAG homemade** — nessun vector database, similarità coseno pura
- **Railway** — deploy e hosting

## Architettura

```
Telegram → bot.py → agent.py → rag.py → file .txt
                             ↘ Groq API → risposta in streaming
```

## Installazione locale

1. Clona il repository
   ```bash
   git clone https://github.com/mariateesa/pasticcerebot-pro.git
   cd pasticcerebot-pro
   ```

2. Installa le dipendenze
   ```bash
   python -m pip install -r requirements.txt
   ```

3. Configura le variabili d'ambiente
   ```bash
   cp .env.example .env
   # inserisci TELEGRAM_TOKEN e GROQ_API_KEY
   ```

4. Avvia il bot
   ```bash
   python bot.py
   ```

## Test

```bash
python -m pip install pytest
python -m pytest test_rag.py -v
```

## Struttura del progetto

```
├── bot.py           # Entry point Telegram
├── agent.py         # Logica agente — RAG + Groq + memoria
├── rag.py           # Motore di ricerca testuale
├── config.py        # Configurazione centralizzata
├── test_rag.py      # Test del sistema RAG
├── data/
│   └── ricette/     # 50+ ricette in formato .txt
└── .env.example
```

## Aggiungere ricette

Crea un file `.txt` in `data/ricette/` con il nome della ricetta
(es. `creme_caramel.txt`). Il bot la rileva automaticamente senza riavvio.

## Versione locale

Esiste anche una versione che gira interamente offline con Ollama:
[pasticcerebot](https://github.com/mariateesa/pasticcerebot)
