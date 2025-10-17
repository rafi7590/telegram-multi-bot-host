import asyncio
import requests
import re
import json
import logging
import sys
import io
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TimedOut

# ===== Windows UTF-8 fix =====
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ===== CONFIG =====
BOT_TOKEN = "8250684252:AAGpXT4xkl9SMvQ4zHCJTDmSTCuB9_pxgNo"
CHAT_IDS = ["-1003063065936"]

API_TOKEN = "Qk9RQjRSQkF3TmpfSVKMVVJfhF1rhnaLYJOLU0qXiUd3VoZ-XYeV"
API_BASE_URL = "http://147.135.212.197/crapi/s1t/viewstats"  # viewstats API
RECORDS_TO_FETCH = 10

POLL_INTERVAL = 15  # seconds

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[logging.StreamHandler(sys.stdout)])

# ===== FULL COUNTRY MAP =====
COUNTRY_MAP = {
    '1': '🇺🇸 USA / Canada',
    '7': '🇷🇺 Russia / Kazakhstan',
    '20': '🇪🇬 Egypt',
    '27': '🇿🇦 South Africa',
    '30': '🇬🇷 Greece',
    '31': '🇳🇱 Netherlands',
    '32': '🇧🇪 Belgium',
    '33': '🇫🇷 France',
    '34': '🇪🇸 Spain',
    '36': '🇭🇺 Hungary',
    '39': '🇮🇹 Italy / Vatican City',
    '40': '🇷🇴 Romania',
    '41': '🇨🇭 Switzerland',
    '43': '🇦🇹 Austria',
    '44': '🇬🇧 United Kingdom',
    '45': '🇩🇰 Denmark',
    '46': '🇸🇪 Sweden',
    '47': '🇳🇴 Norway / Svalbard',
    '48': '🇵🇱 Poland',
    '49': '🇩🇪 Germany',
    '51': '🇵🇪 Peru',
    '52': '🇲🇽 Mexico',
    '53': '🇨🇺 Cuba',
    '54': '🇦🇷 Argentina',
    '55': '🇧🇷 Brazil',
    '56': '🇨🇱 Chile',
    '57': '🇨🇴 Colombia',
    '58': '🇻🇪 Venezuela',
    '60': '🇲🇾 Malaysia',
    '61': '🇦🇺 Australia / Christmas Island',
    '62': '🇮🇩 Indonesia',
    '63': '🇵🇭 Philippines',
    '64': '🇳🇿 New Zealand / Pitcairn Islands',
    '65': '🇸🇬 Singapore',
    '66': '🇹🇭 Thailand',
    '81': '🇯🇵 Japan',
    '82': '🇰🇷 South Korea',
    '84': '🇻🇳 Vietnam',
    '86': '🇨🇳 China',
    '90': '🇹🇷 Turkey',
    '91': '🇮🇳 India',
    '92': '🇵🇰 Pakistan',
    '93': '🇦🇫 Afghanistan',
    '94': '🇱🇰 Sri Lanka',
    '95': '🇲🇲 Myanmar',
    '98': '🇮🇷 Iran',
    '211': '🇸🇸 South Sudan',
    '212': '🇲🇦 Morocco / Western Sahara',
    '213': '🇩🇿 Algeria',
    '216': '🇹🇳 Tunisia',
    '218': '🇱🇾 Libya',
    '220': '🇬🇲 Gambia',
    '221': '🇸🇳 Senegal',
    '222': '🇲🇷 Mauritania',
    '223': '🇲🇱 Mali',
    '224': '🇬🇳 Guinea',
    '225': "🇨🇮 Côte d'Ivoire",
    '226': '🇧🇫 Burkina Faso',
    '227': '🇳🇪 Niger',
    '228': '🇹🇬 Togo',
    '229': '🇧🇯 Benin',
    '230': '🇲🇺 Mauritius',
    '231': '🇱🇷 Liberia',
    '232': '🇸🇱 Sierra Leone',
    '233': '🇬🇭 Ghana',
    '234': '🇳🇬 Nigeria',
    '235': '🇹🇩 Chad',
    '236': '🇨🇫 Central African Republic',
    '237': '🇨🇲 Cameroon',
    '238': '🇨🇻 Cape Verde',
    '239': '🇸🇹 Sao Tome & Principe',
    '240': '🇬🇶 Equatorial Guinea',
    '241': '🇬🇦 Gabon',
    '242': '🇨🇬 Congo',
    '243': '🇨🇩 DR Congo',
    '244': '🇦🇴 Angola',
    '245': '🇬🇼 Guinea-Bissau',
    '246': '🇮🇴 British Indian Ocean Territory',
    '248': '🇸🇨 Seychelles',
    '249': '🇸🇩 Sudan',
    '250': '🇷🇼 Rwanda',
    '251': '🇪🇹 Ethiopia',
    '252': '🇸🇴 Somalia',
    '253': '🇩🇯 Djibouti',
    '254': '🇰🇪 Kenya',
    '255': '🇹🇿 Tanzania',
    '256': '🇺🇬 Uganda',
    '257': '🇧🇮 Burundi',
    '258': '🇲🇿 Mozambique',
    '260': '🇿🇲 Zambia',
    '261': '🇲🇬 Madagascar',
    '262': '🇷🇪 Réunion / Mayotte',
    '263': '🇿🇼 Zimbabwe',
    '264': '🇳🇦 Namibia',
    '265': '🇲🇼 Malawi',
    '266': '🇱🇸 Lesotho',
    '267': '🇧🇼 Botswana',
    '268': '🇸🇿 Eswatini',
    '269': '🇰🇲 Comoros',
    '290': '🇸🇭 Saint Helena / Tristan da Cunha',
    '291': '🇪🇷 Eritrea',
    '297': '🇦🇼 Aruba',
    '298': '🇫🇴 Faroe Islands',
    '299': '🇬🇱 Greenland',
    '350': '🇬🇮 Gibraltar',
    '351': '🇵🇹 Portugal',
    '352': '🇱🇺 Luxembourg',
    '353': '🇮🇪 Ireland',
    '354': '🇮🇸 Iceland',
    '355': '🇦🇱 Albania',
    '356': '🇲🇹 Malta',
    '357': '🇨🇾 Cyprus',
    '358': '🇫🇮 Finland / Åland Islands',
    '359': '🇧🇬 Bulgaria',
    '370': '🇱🇹 Lithuania',
    '371': '🇱🇻 Latvia',
    '372': '🇪🇪 Estonia',
    '373': '🇲🇩 Moldova',
    '374': '🇦🇲 Armenia',
    '375': '🇧🇾 Belarus',
    '376': '🇦🇩 Andorra',
    '377': '🇲🇨 Monaco',
    '378': '🇸🇲 San Marino',
    '379': '🇻🇦 Vatican City',
    '380': '🇺🇦 Ukraine',
    '381': '🇷🇸 Serbia',
    '382': '🇲🇪 Montenegro',
    '383': '🇽🇰 Kosovo',
    '385': '🇭🇷 Croatia',
    '386': '🇸🇮 Slovenia',
    '387': '🇧🇦 Bosnia & Herzegovina',
    '389': '🇲🇰 North Macedonia',
    '420': '🇨🇿 Czech Republic',
    '421': '🇸🇰 Slovakia',
    '423': '🇱🇮 Liechtenstein',
    '500': '🇫🇰 Falkland Islands',
    '501': '🇧🇿 Belize',
    '502': '🇬🇹 Guatemala',
    '503': '🇸🇻 El Salvador',
    '504': '🇭🇳 Honduras',
    '505': '🇳🇮 Nicaragua',
    '506': '🇨🇷 Costa Rica',
    '507': '🇵🇦 Panama',
    '509': '🇭🇹 Haiti',
    '590': '🇬🇵 Guadeloupe / Saint Barthélemy / Saint Martin',
    '591': '🇧🇴 Bolivia',
    '592': '🇬🇾 Guyana',
    '593': '🇪🇨 Ecuador',
    '594': '🇬🇫 French Guiana',
    '595': '🇵🇾 Paraguay',
    '596': '🇲🇶 Martinique',
    '597': '🇸🇷 Suriname',
    '598': '🇺🇾 Uruguay',
    '670': '🇹🇱 Timor-Leste',
    '673': '🇧🇳 Brunei',
    '674': '🇳🇷 Nauru',
    '675': '🇵🇬 Papua New Guinea',
    '676': '🇹🇴 Tonga',
    '677': '🇸🇧 Solomon Islands',
    '678': '🇻🇺 Vanuatu',
    '679': '🇫🇯 Fiji',
    '680': '🇵🇼 Palau',
    '681': '🇼🇫 Wallis and Futuna',
    '682': '🇨🇰 Cook Islands',
    '683': '🇳🇺 Niue',
    '685': '🇼🇸 Samoa',
    '686': '🇰🇮 Kiribati',
    '687': '🇳🇨 New Caledonia',
    '688': '🇹🇻 Tuvalu',
    '689': '🇵🇫 French Polynesia',
    '690': '🇹🇰 Tokelau',
    '691': '🇫🇲 Micronesia',
    '692': '🇲🇭 Marshall Islands',
    '850': '🇰🇵 North Korea',
    '852': '🇭🇰 Hong Kong',
    '853': '🇲🇴 Macau',
    '855': '🇰🇭 Cambodia',
    '856': '🇱🇦 Laos',
    '870': '🌍 Inmarsat',
    '880': '🇧🇩 Bangladesh',
    '886': '🇹🇼 Taiwan',
    '960': '🇲🇻 Maldives',
    '961': '🇱🇧 Lebanon',
    '962': '🇯🇴 Jordan',
    '963': '🇸🇾 Syria',
    '964': '🇮🇶 Iraq',
    '965': '🇰🇼 Kuwait',
    '966': '🇸🇦 Saudi Arabia',
    '967': '🇾🇪 Yemen',
    '968': '🇴🇲 Oman',
    '970': '🇵🇸 Palestine',
    '971': '🇦🇪 UAE',
    '972': '🇮🇱 Israel',
    '973': '🇧🇭 Bahrain',
    '974': '🇶🇦 Qatar',
    '975': '🇧🇹 Bhutan',
    '976': '🇲🇳 Mongolia',
    '977': '🇳🇵 Nepal',
    '992': '🇹🇯 Tajikistan',
    '993': '🇹🇲 Turkmenistan',
    '994': '🇦🇿 Azerbaijan',
    '995': '🇬🇪 Georgia',
    '996': '🇰🇬 Kyrgyzstan',
    '998': '🇺🇿 Uzbekistan',
}

# ===== Helpers =====
def clean_number(number: str) -> str:
    return re.sub(r"\D", "", number)

def get_country_from_number(number: str) -> str:
    cleaned = clean_number(number)
    for code in sorted(COUNTRY_MAP.keys(), key=lambda x: -len(x)):
        if cleaned.startswith(code):
            return COUNTRY_MAP[code]
    return "🌍 Unknown"

def mask_number(number: str) -> str:
    cleaned = clean_number(number)
    for code in sorted(COUNTRY_MAP.keys(), key=lambda x: -len(x)):
        if cleaned.startswith(code):
            country_len = len(code)
            if len(cleaned) > country_len + 3:
                return f"+{code}{'X' * (len(cleaned) - country_len - 3)}{cleaned[-3:]}"
            else:
                return f"+{code}{cleaned[-3:]}"
    return f"+{cleaned[:3]}{'X' * (len(cleaned) - 3)}{cleaned[-3:]}"

# ===== Already sent store =====
def save_already_sent(already_sent):
    with open("already_sent.json", "w", encoding="utf-8") as f:
        json.dump(list(already_sent), f, ensure_ascii=False)

def load_already_sent():
    try:
        with open("already_sent.json", "r", encoding="utf-8") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

already_sent = load_already_sent()

# ===== Platform Detection =====
def detect_platform_from_message(message: str) -> str:
    text = message.lower()
    if "whatsapp" in text:
        return "WHATSAPP"
    elif "facebook" in text:
        return "FACEBOOK"
    elif "telegram" in text:
        return "TELEGRAM"
    elif "instagram" in text:
        return "INSTAGRAM"
    elif "twitter" in text or "x.com" in text:
        return "TWITTER"
    elif "gmail" in text or "google" in text:
        return "GOOGLE"
    elif "tiktok" in text:
        return "TIKTOK"
    elif "microsoft" in text or "outlook" in text or "hotmail" in text:
        return "MICROSOFT"
    else:
        return "UNKNOWN"

# ===== API fetch =====
def fetch_messages():
    try:
        params = {
            "token": API_TOKEN,
            "records": RECORDS_TO_FETCH
        }
        resp = requests.get(API_BASE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        print("\n=== RAW API RESPONSE ===")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        if data.get("status") == "success":
            return data.get("data", [])
        return []
    except Exception as e:
        logging.error(f"Fetch error: {e}")
        return []

# ===== OTP extraction =====
def extract_otp(text):
    if not text:
        return None
    # সব ধরনের OTP ধরবে, ড্যাশসহ
    match = re.search(r"(\d+(?:-\d+)*)", text)
    if match:
        # পুরো OTP 그대로 ফেরত দেবে, ড্যাশসহ
        return match.group(1)
    return None

# ===== Send messages =====
async def send_messages():
    messages = fetch_messages()
    if not messages:
        logging.info("No new messages.")
        return

    for item in messages:
        try:
            date = item.get("dt", "")
            number = item.get("num", "")
            service = detect_platform_from_message(item.get("message", "")) or item.get("cli", "")
            message = item.get("message", "")

            otp = extract_otp(message)
            if not otp:
                continue

            unique_key = f"{number}|{otp}"
            if unique_key in already_sent:
                continue

            already_sent.add(unique_key)
            save_already_sent(already_sent)

            masked_number = mask_number(number)
            country = get_country_from_number(number)

            caption = (
                "㊗️ <b>Social Media OTP Received</b> ㊗️\n\n"
                f"⏳ <b>Time:</b> <code>{date}</code>\n"
                f"☎️ <b>Platform:</b> <code>{service}</code>\n"
                f"📞 <b>Number:</b> <code>{masked_number}</code>\n"
                f"🪪 <b>Country:</b> {country}\n"
                f"🔑 <b>OTP Code:</b> <code>{otp}</code>\n"
                f"📝 <b>Message:</b> <i>{message}</i>\n\n"
                "㊙️ <b>RAFI-<a href=\"https://t.me/oiwdiscussion\">ONLINE-EARNING</a> ㊙️</b>"
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("👨‍💻 Bot Developer", url="https://t.me/MethodProvider")],
                [InlineKeyboardButton("Number Channel", url="https://t.me/oiwnumber")]
            ])

            for chat_id in CHAT_IDS:
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text=caption,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                        reply_markup=keyboard
                    )
                    logging.info(f"✓ Sent OTP {otp} to {chat_id}")
                except TimedOut:
                    logging.error(f"⌛ Timeout sending to {chat_id}")
                except Exception as e:
                    logging.error(f"⚠️ Error sending to {chat_id}: {str(e)}")

            await asyncio.sleep(1)

        except Exception as e:
            logging.error(f"Error processing item: {e}")

# ===== Main loop =====
async def main():
    logging.info("Starting OTP notifier...")
    while True:
        await send_messages()
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    asyncio.run(main())
