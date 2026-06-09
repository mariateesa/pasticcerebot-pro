import asyncio
import json
import logging
import os
import threading
import time
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from config import TELEGRAM_TOKEN, RICETTE_DIR
from agent import rispondi_stream, reset_memoria

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

CHAT_IDS_FILE = os.path.join(os.path.dirname(__file__), "chat_ids.json")


def carica_chat_ids() -> set:
    if os.path.exists(CHAT_IDS_FILE):
        with open(CHAT_IDS_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def salva_chat_ids(ids: set) -> None:
    with open(CHAT_IDS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f)


chat_ids = carica_chat_ids()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_ids.add(update.effective_chat.id)
    salva_chat_ids(chat_ids)
    await update.message.reply_text(
        "Ciao! Sono PasticcereBot!\n"
        "Chiedimi qualsiasi cosa sulle ricette di pasticceria!\n\n"
        "Comandi disponibili:\n"
        "/lista — tutte le ricette\n"
        "/cerca <ingrediente> — ricette per ingrediente\n"
        "/reset — cancella la memoria della chat"
    )


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reset_memoria(update.effective_chat.id)
    await update.message.reply_text("Memoria cancellata! Ripartiamo da zero.")


async def lista(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    files = sorted(f for f in os.listdir(RICETTE_DIR) if f.endswith(".txt"))
    if not files:
        await update.message.reply_text("Non ho ancora nessuna ricetta.")
        return
    nomi = "\n".join(
        f"• {os.path.splitext(f)[0].replace('_', ' ').title()}" for f in files
    )
    await update.message.reply_text(f"Ricette disponibili:\n\n{nomi}")


async def cerca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Specifica un ingrediente.\nEs: /cerca uova")
        return

    ingrediente = " ".join(context.args).lower()
    trovate = []

    for nome_file in os.listdir(RICETTE_DIR):
        if not nome_file.endswith(".txt"):
            continue
        with open(os.path.join(RICETTE_DIR, nome_file), encoding="utf-8") as f:
            testo = f.read()
        if ingrediente in testo.lower():
            nome = os.path.splitext(nome_file)[0].replace("_", " ").title()
            trovate.append(nome)

    if trovate:
        elenco = "\n".join(f"• {n}" for n in sorted(trovate))
        await update.message.reply_text(
            f"Ricette con '{ingrediente}' ({len(trovate)} trovate):\n\n{elenco}"
        )
    else:
        await update.message.reply_text(f"Nessuna ricetta con '{ingrediente}' trovata.")


async def gestisci_messaggio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_ids.add(update.effective_chat.id)
    salva_chat_ids(chat_ids)

    domanda = update.message.text
    chat_id = update.effective_chat.id
    loop = asyncio.get_event_loop()

    msg = await update.message.reply_text("...")
    queue: asyncio.Queue = asyncio.Queue()

    def groq_thread():
        for token in rispondi_stream(domanda, chat_id):
            loop.call_soon_threadsafe(queue.put_nowait, token)
        loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=groq_thread, daemon=True).start()

    testo = ""
    ultimo_aggiornamento = time.time()
    INTERVALLO = 1.5

    while True:
        token = await queue.get()
        if token is None:
            break
        testo += token
        ora = time.time()
        if ora - ultimo_aggiornamento >= INTERVALLO and testo.strip():
            try:
                await msg.edit_text(testo)
                ultimo_aggiornamento = ora
            except Exception:
                pass

    if testo.strip():
        try:
            await msg.edit_text(testo)
        except Exception:
            pass


async def notifica_spegnimento(app) -> None:
    for chat_id in chat_ids:
        try:
            await app.bot.send_message(chat_id=chat_id, text="PasticcereBot si e' spento.")
        except Exception:
            pass


async def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("lista", lista))
    app.add_handler(CommandHandler("cerca", cerca))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gestisci_messaggio))
    print("PasticcereBot PRO avviato (Groq). Premi Ctrl+C per fermare.")
    async with app:
        await app.start()
        await app.updater.start_polling()
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            await notifica_spegnimento(app)
            await app.updater.stop()
            await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
