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
PIX_MENSAL = "00020126360014br.gov.bcb.pix0114+5542991376372520400005303986540514.995802BR5910Joao Alves6009Sao Paulo62230519daqr2789155863177436304203B"
PIX_TRIMESTRAL = "00020126580014br.gov.bcb.pix013687f579d7-4382-435a-aae0-eced225a9d36520400005303986540529.905802BR5910Joao Alves6009Sao Paulo62230519daqr27891558615494763040A04"

CANAL_ID = -1002432070371
ADMIN_ID = 357026423
VIDEO_ID = "BAACAgEAAxkBAAEaY_9peBWHLj03SozqzKiU7Vk2WMngHwAC1wUAAvobwEc6uAQNHhIvPTgE"

# Banco de dados
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

    if plano == "mensal":
        pix = PIX_MENSAL
        valor = "R$ 14,99"
        periodo = "30 dias"
    else:
        pix = PIX_TRIMESTRAL
        valor = "R$ 29,90"
        periodo = "90 dias"

    texto = (
        f"✨ *Plano {plano.upper()}*\n\n"
        f"📆 Validade: *{periodo}*\n"
        f"💰 Valor: *{valor}*\n\n"
        "💳 *Pagamento via Pix*\n"
        f"`{pix}`\n\n"
        "📸 Envie o comprovante aqui após o pagamento."
    )

    await query.message.reply_text(texto, parse_mode="Markdown")


async def comprovante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    plano = context.user_data.get("plano")

    if not plano:
        await update.message.reply_text(
            "❌ Não identifiquei seu plano.\nUse /start e escolha novamente."
        )
        return

    # Define validade conforme plano
    dias = 30 if plano == "mensal" else 90
    expira = datetime.now() + timedelta(days=dias)

    # Salva no banco
    cur.execute(
        "INSERT INTO usuarios VALUES (?, ?, ?)",
        (user.id, plano, expira.isoformat())
    )
    conn.commit()

    # Cria link único do canal
    link = await context.bot.create_chat_invite_link(
        chat_id=CANAL_ID,
        member_limit=1,
        expire_date=int((datetime.now() + timedelta(minutes=10)).timestamp())
    )

    # Envia link ao usuário
    await update.message.reply_text(
        "✅ *Pagamento recebido!*\n\n"
        "🔐 Acesse o canal privado pelo link abaixo:\n"
        f"{link.invite_link}\n\n"
        "⏳ *O link expira em 10 minutos*.",
        parse_mode="Markdown"
    )

    # Notifica admin
    await context.bot.send_message(
        ADMIN_ID,
        f"Novo acesso liberado:\n"
        f"Usuário: @{user.username}\n"
        f"ID: {user.id}\n"
        f"Plano: {plano}"
    )


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(escolher_plano, pattern="^(mensal|trimestral)$"))
app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, comprovante))

app.run_polling()
