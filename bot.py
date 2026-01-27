from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
import sqlite3
from datetime import datetime, timedelta

TOKEN = "7776890109:AAGULnL1cUiDKLikBTSduM7BcAQqAV12mfc"
PIX_CHAVE = "00020126360014br.gov.bcb.pix0114+5542991376372520400005303986540514.995802BR5910Joao Alves6009Sao Paulo62230519daqr2789155863177436304203B"
CANAL_ID = -1002432070371
ADMIN_ID = 357026423
VIDEO_ID = "BAACAgEAAxkBAAEaY_9peBWHLj03SozqzKiU7Vk2WMngHwAC1wUAAvobwEc6uAQNHhIvPTgE"

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    user_id INTEGER,
    plano TEXT,
    expira_em TEXT
)
""")
conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teclado = [
        [InlineKeyboardButton("🔥 Mensal", callback_data="mensal")],
        [InlineKeyboardButton("💎 Trimestral", callback_data="trimestral")]
    ]

    await context.bot.send_video(
        chat_id=update.effective_chat.id,
        video=VIDEO_ID,
        caption=(
            "🔥 *Bem-vindo!* 🔥\n\n"
            "Tenha acesso agora a *milhares de conteúdos selecionados*,\n"
            "que você *não encontra na web*.\n\n"
            "*Escolha seu plano abaixo:* 👇"
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(teclado)
    )

async def escolher_plano(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    plano = query.data
    context.user_data["plano"] = plano

    texto = (
        f"✨ *Plano {plano.upper()}*\n\n"
        "💰 *Pagamento via Pix*\n"
        f"`{PIX_CHAVE}`\n\n"
        "📸 Envie o comprovante aqui após o pagamento."
    )

    await query.message.reply_text(texto, parse_mode="Markdown")

async def comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plano = context.user_data.get("plano")
    user = update.message.from_user

    await context.bot.send_message(
        ADMIN_ID,
        f"Pagamento pendente:\n"
        f"Usuário: @{user.username}\n"
        f"Plano: {plano}\n\n"
        f"/aprovar_{user.id}"
    )

    await update.message.reply_text("Comprovante recebido. Aguarde confirmação.")

async def aprovar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    user_id = int(update.message.text.split("_")[1])
    dias = 30

    expira = datetime.now() + timedelta(days=dias)

    cur.execute(
        "INSERT INTO usuarios VALUES (?, ?, ?)",
        (user_id, "ativo", expira.isoformat())
    )
    conn.commit()

    link = await context.bot.create_chat_invite_link(
        CANAL_ID,
        member_limit=1,
        expire_date=int((datetime.now() + timedelta(minutes=10)).timestamp())
    )

    await context.bot.send_message(
        user_id,
        f"Pagamento confirmado.\n\nAcesse o canal:\n{link.invite_link}"
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(escolher_plano, pattern="^(mensal|trimestral)$"))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, comprovante))
app.add_handler(MessageHandler(filters.Regex("^/aprovar_"), aprovar))
app.run_polling()
