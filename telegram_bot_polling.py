import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("No se encontró BOT_TOKEN en .env")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    # envía mensaje y muestra el chat_id en consola para que lo copies
    await update.message.reply_text(f"Hola, soy Jarvis. Tu chat_id es: {chat_id}")
    print("Nuevo /start desde chat_id:", chat_id)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - inicia\n/help - ayuda\n/tuitea <texto> - ejemplo de comando")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    # solo eco por ahora
    await update.message.reply_text(f"Echo: {text}")
    print(f"Mensaje recibido de {update.effective_chat.id}: {text}")

# Ejemplo: comando que ejecuta una acción de Jarvis (placeholder)
async def tuitea_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usa: /tuitea texto a tuitear")
        return
    texto = " ".join(args)
    # Aquí llamas a la función real de Jarvis que publique en Twitter/X
    # Por ejemplo: jarvis.publish_tweet(texto)  <-- integra tu función
    await update.message.reply_text(f"(Simulación) Tuiteando: {texto}")
    print(f"Comando /tuitea: {texto} (chat {update.effective_chat.id})")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("tuitea", tuitea_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo))
    print("Bot iniciado (polling). Envía /start al bot desde Telegram para obtener tu chat_id.")
    app.run_polling()

if __name__ == "__main__":
    main()