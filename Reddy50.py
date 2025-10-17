import sys
import os
import json
import random
import asyncio
from datetime import datetime
import aiohttp

# ✅ Always work from script directory
os.chdir(os.path.dirname(__file__))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

sys.stdout.reconfigure(encoding='utf-8')

# ---------------- CONFIG ----------------
BOT_TOKEN = "8266523697:AAGAWGtYEOEXRRrNl3wJ0lvlMk9Q7y40wd8"
ADMIN_ID = 6000804411
GROUP_ID = -1002769183705
DATA_FILE = "bot_data.json"

# ---------------- DATA ----------------
COUNTRIES = {}
ASSIGNED_NUMBERS = {}
USED_NUMBERS = set()
USERS = set()
API_TOKENS = {"s1t": "Qk9RQjRSQkF3TmpfSVKMVVJfhF1rhnaLYJOLU0qXiUd3VoZ-XYeV"}


# ---------------- SESSION ----------------
_session = None
async def get_session():
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


# ---------------- STORAGE ----------------
def load_data():
    global COUNTRIES, USED_NUMBERS, USERS
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                COUNTRIES.update(d.get("countries", {}))
                USED_NUMBERS.update(d.get("used_numbers", []))
                USERS.update(d.get("users", []))
        except Exception as e:
            print("Failed to load data:", e)

def save_data():
    try:
        d = {
            "countries": COUNTRIES,
            "used_numbers": list(USED_NUMBERS),
            "users": list(USERS)
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Failed to save data:", e)


# ---------------- TELEGRAM HANDLERS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in USERS:
        USERS.add(user_id)
        save_data()

    keyboard = []
    for code, data in COUNTRIES.items():
        count = len([n for n in data.get("numbers", []) if n not in USED_NUMBERS])
        keyboard.append([InlineKeyboardButton(f"{data['flag']} +{code} {data['name']} [{count}]",
                                              callback_data=f"country:{code}")])
    if not keyboard:
        text = "❌ No countries available. Admin must add one."
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query:
            await update.callback_query.message.reply_text(text)
        return

    text = "🌍 Select country:"
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ---------------- CALLBACK HANDLER ----------------
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = update.effective_user.id
    data = query.data
    app = context.application

    try:
        await query.answer(cache_time=1)
    except Exception as e:
        print(f"⚠️ Callback answer error: {e}", flush=True)

    if data.startswith("country:") or data.startswith("change_number:"):
        change = data.startswith("change_number:")
        _, country_code = data.split(":", 1)
        country = COUNTRIES.get(country_code)
        if not country:
            await query.edit_message_text("❌ Country not found.")
            return

        all_numbers = [n for n in country.get("numbers", []) if n not in USED_NUMBERS]
        if not all_numbers:
            await query.edit_message_text("❌ No available numbers right now.")
            return

        pick = random.choice(all_numbers)
        USED_NUMBERS.add(pick)
        save_data()

        text = f"{country['flag']} {country['name']} Number {'Changed' if change else 'Assigned'}:\n<code>+{pick}</code>\n\nWaiting for OTP…"
        msg = await query.edit_message_text(
            text=text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔁 Change Number", callback_data=f"change_number:{country_code}")],
                [InlineKeyboardButton("🌍 Change Country", callback_data="back_to_countries")]
            ])
        )

        ASSIGNED_NUMBERS[user_id] = {"country": country_code, "number": pick, "otp": None, "message": msg}
        asyncio.create_task(auto_check_otp(user_id, app))
        return

    if data == "back_to_countries":
        await start(update, context)
        return


# ---------------- OTP AUTO CHECK (FULL SHOW + COMPLETE OTP) ----------------
async def auto_check_otp(user_id: int, app):
    assigned = ASSIGNED_NUMBERS.get(user_id)
    if not assigned:
        return

    number = assigned["number"]
    country_code = assigned["country"]
    country = COUNTRIES.get(country_code, {})
    token = API_TOKENS.get("s1t")
    if not token:
        print("❌ No API token configured for s1t", flush=True)
        return

    url = f"http://147.135.212.197/crapi/s1t/viewstats?token={token}&filternum={number}&records=1"
    otp = None
    platform = "Unknown"
    message = ""
    session = await get_session()

    for _ in range(12):  # 12 বার চেষ্টা (৫ সেকেন্ড করে)
        try:
            async with session.get(url, timeout=15) as resp:
                data = await resp.json()
                records = data.get("data", [])
                if records:
                    last = records[-1]
                    message = last.get("message", "") or ""
                    platform = last.get("cli") or last.get("service") or last.get("platform") or platform

                    msg_lower = message.lower()
                    if "whatsapp" in msg_lower:
                        platform = "WHATSAPP"
                    elif "facebook" in msg_lower:
                        platform = "FACEBOOK"
                    elif "instagram" in msg_lower:
                        platform = "INSTAGRAM"
                    elif "telegram" in msg_lower:
                        platform = "TELEGRAM"
                    elif "tiktok" in msg_lower:
                        platform = "TIKTOK"

                    import re
                    # ✅ এখন সম্পূর্ণ কোড যেমন 941-835, 1234 5678, 55667788 সব ধরবে
                    otp_match = re.search(r"\b\d{2,8}(?:[-\s]?\d{2,8})+\b", message)
                    otp = otp_match.group(0) if otp_match else None

                    if otp:
                        break
        except Exception as e:
            print(f"⚠️ OTP fetch error: {e}", flush=True)
        await asyncio.sleep(5)

    if not otp:
        print(f"❌ OTP not received for +{number}", flush=True)
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bot = app.bot
    masked_number = f"{number[:4]}XXXXXX{number[-4:]}"

    # HTML safe
    safe_message = (
        message.replace("&", "&amp;")
               .replace("<", "&lt;")
               .replace(">", "&gt;")
    )

    # ---------- USER ----------
    user_msg = (
        f"{country.get('flag','')} {country.get('name','')} Number Assigned:\n"
        f"<code>+{number}</code>\n\n"
        f"✅ OTP Received: <b>{otp}</b>\n"
        f"⏳ Platform: <code>{platform}</code>\n"
        f"📝 Message:\n<code>{safe_message}</code>"
    )

    try:
        await assigned["message"].edit_text(user_msg, parse_mode="HTML")
    except Exception:
        await bot.send_message(chat_id=user_id, text=user_msg, parse_mode="HTML")

    # ---------- GROUP ----------
    group_text = (
        f"㊗️ Social Media OTP Received ㊗️\n\n"
        f"⏳ Time: {now}\n"
        f"☎️ Platform: {platform}\n"
        f"📞 Number: +{masked_number}\n"
        f"🪪 Country: {country.get('flag','')} {country.get('name','')}\n"
        f"🔑 OTP Code: <b>{otp}</b>\n"
        f"📝 Message:\n<code>{safe_message}</code>\n\n"
        f'㊙️ <b>RAFI-<a href="https://t.me/numberchanel0">ONLINE-EARNING</a> ㊙️</b>'
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("👨‍💻 Bot Panel", url="https://t.me/otptest102_bot")],
        [InlineKeyboardButton("Number Channel", url="https://t.me/NUMBERGROUP2")]
    ])

    try:
        await bot.send_message(chat_id=GROUP_ID, text=group_text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        pass

    USED_NUMBERS.add(number)
    ASSIGNED_NUMBERS.pop(user_id, None)
    save_data()


# ---------------- ADMIN COMMANDS ----------------
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    msg_text = " ".join(context.args)
    bot = context.bot
    sent_count = 0

    for u in list(USERS):
        try:
            await bot.send_message(chat_id=u, text=msg_text)
            sent_count += 1
        except Exception:
            pass

    try:
        await bot.send_message(chat_id=GROUP_ID, text=msg_text)
    except Exception:
        pass

    await update.message.reply_text(f"✅ Broadcast sent to {sent_count} users and group.")

async def add_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /addcountry <AreaCode> <CountryName> <FlagEmoji>")
        return
    code, name, flag = context.args[0], context.args[1], context.args[2]
    COUNTRIES[code] = {"name": name, "flag": flag, "numbers": []}
    save_data()
    await update.message.reply_text(f"✅ Country added: {flag} {name} (+{code})")

async def remove_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    code = context.args[0]
    if code in COUNTRIES:
        del COUNTRIES[code]
        save_data()
        await update.message.reply_text(f"✅ Country +{code} removed.")
    else:
        await update.message.reply_text("❌ Country not found.")

async def add_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    code = context.args[0]
    numbers = context.args[1:]
    if code in COUNTRIES:
        COUNTRIES[code]["numbers"].extend(numbers)
        save_data()
        await update.message.reply_text(f"✅ Added {len(numbers)} numbers to +{code}.")
    else:
        await update.message.reply_text("❌ Country not found.")

async def remove_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    code = context.args[0]
    numbers = context.args[1:]
    if code in COUNTRIES:
        COUNTRIES[code]["numbers"] = [n for n in COUNTRIES[code]["numbers"] if n not in numbers]
        save_data()
        await update.message.reply_text(f"✅ Removed {len(numbers)} numbers from +{code}.")
    else:
        await update.message.reply_text("❌ Country not found.")

async def clearnumbers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /clearnumbers <AreaCode>")
        return
    code = context.args[0]
    if code in COUNTRIES:
        count = len(COUNTRIES[code]["numbers"])
        COUNTRIES[code]["numbers"].clear()
        save_data()
        await update.message.reply_text(f"✅ Removed all {count} numbers from +{code}.")
    else:
        await update.message.reply_text("❌ Country not found.")

async def resetused(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    USED_NUMBERS.clear()
    save_data()
    await update.message.reply_text("✅ Reset all used numbers.")

async def add_numbers_from_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addnumbersfile <AreaCode> <filename>")
        return
    code, filename = context.args[0], context.args[1]
    if code not in COUNTRIES:
        await update.message.reply_text("❌ Country not found.")
        return
    if not os.path.exists(filename):
        await update.message.reply_text(f"❌ File {filename} not found.")
        return
    with open(filename, "r", encoding="utf-8") as f:
        numbers = [line.strip() for line in f if line.strip()]
    COUNTRIES[code]["numbers"].extend(numbers)
    save_data()
    await update.message.reply_text(f"✅ Added {len(numbers)} numbers to +{code}.")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    load_data()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User commands
    app.add_handler(CommandHandler("start", start))

    # Admin commands
    app.add_handler(CommandHandler("addcountry", add_country))
    app.add_handler(CommandHandler("removecountry", remove_country))
    app.add_handler(CommandHandler("addnumber", add_number))
    app.add_handler(CommandHandler("removenumber", remove_number))
    app.add_handler(CommandHandler("resetused", resetused))
    app.add_handler(CommandHandler("addnumbersfile", add_numbers_from_file))
    app.add_handler(CommandHandler("clearnumbers", clearnumbers))
    app.add_handler(CommandHandler("broadcast", broadcast))

    # Callback query
    app.add_handler(CallbackQueryHandler(callback_handler))

    print("RAFI Bot running...")
    app.run_polling()
