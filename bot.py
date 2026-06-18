import telebot
from telebot import types
import random
import time
import string
import json
from datetime import datetime, timedelta
import requests
import hashlib
import io
import base64
import urllib.parse

# ============================================================
# 👺 تنظیمات ربات v7.3 Fixed
# ============================================================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@DR_Gojo_Satoru")
CHANNEL_LINK = os.getenv("CHANNEL_LINK", "https://t.me/DR_Gojo_Satoru")
GROUP_LINK = os.getenv("GROUP_LINK", "https://t.me/+tddIoHyVNUY2MDM0")
OWNER_ID = int(os.getenv("OWNER_ID", "7097495720"))
GROQ_KEY = os.getenv("GROQ_KEY")
TOGETHER_KEY = os.getenv("TOGETHER_KEY")
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================
# 📊 دیتابیس
# ============================================================
users = {}
warnings = {}
chat_histories = {}
ai_chat_users = set()
ai_last_active = {}
cooldowns = {}
whisper_data = {}
confession_count = {}
user_points = {}
user_level = {}
user_states = {}
gift_codes = {}
banned_users = set()
confession_reactions = {}
user_selected_model = {}

# 🆕 دیتابیس جدید برای دعوت و ریپلای AI
user_invites = {}  # {user_id: {'count': 0, 'invited_users': []}}
timed_ranks = {}  # {user_id: {'rank': 'plus', 'expires': datetime}}
ai_last_message = {}  # {user_id: message_id} برای ریپلای AI
ai_context = {}  # 🆕 ذخیره context برای ریپلای

AI_TIMEOUT = 180
MAX_AI_QUESTIONS = 10

# ============================================================
# 🤖 سیستم چند مدل AI - با مدل‌های رایگان کارآمد
# ============================================================
AI_MODELS = {
    1: {
        'id': 'llama70',
        'name': '👑 Llama 3.3 70B',
        'model': 'llama-3.3-70b-versatile',
        'tokens': 4096,
        'temp': 0.9,
        'min_rank': 'owner'
    },
    2: {
        'id': 'llama70s',
        'name': '⚔️ Llama 3.1 70B',
        'model': 'llama-3.1-70b-versatile',
        'tokens': 4096,
        'temp': 0.85,
        'min_rank': 'admin'
    },
    3: {
        'id': 'deepseek',
        'name': '🔮 DeepSeek R1',
        'model': 'deepseek-r1-distill-llama-70b',
        'tokens': 3072,
        'temp': 0.8,
        'min_rank': 'legend'
    },
    4: {
        'id': 'mixtral',
        'name': '💎 Mixtral 8x7B',
        'model': 'mixtral-8x7b-32768',
        'tokens': 2048,
        'temp': 0.75,
        'min_rank': 'vip'
    },
    5: {
        'id': 'gemma9',
        'name': '💜 Gemma 2 9B',
        'model': 'gemma2-9b-it',
        'tokens': 2048,
        'temp': 0.7,
        'min_rank': 'premium'
    },
    6: {
        'id': 'llama8',
        'name': '⭐ Llama 3.1 8B',
        'model': 'llama-3.1-8b-instant',
        'tokens': 1024,
        'temp': 0.7,
        'min_rank': 'plus'
    },
    7: {
        'id': 'llama8free',
        'name': '👤 Llama 3 8B (رایگان)',
        'model': 'llama3-8b-8192',
        'tokens': 512,
        'temp': 0.7,
        'min_rank': 'user'
    },
}

RANK_LEVELS = {
    'owner': 7, 'admin': 6, 'legend': 5, 'vip': 4,
    'premium': 3, 'plus': 2, 'user': 1
}

# ============================================================
# 🎯 تنظیمات سیستم دعوت
# ============================================================
INVITE_REWARDS = {
    3: {'rank': 'plus', 'days': 15, 'name': '⭐ پلاس'},
    7: {'rank': 'premium', 'days': 15, 'name': '💜 پریمیوم'},
    15: {'rank': 'vip', 'days': 15, 'name': '💎 ویژه'},
    30: {'rank': 'legend', 'days': 15, 'name': '🔮 افسانه'},
}

# ============================================================
# 🏆 سیستم رنک‌ها
# ============================================================
ranks = {
    'owners': [7097495720],
    'admins': [],
    'legend': [],
    'vip': [],
    'premium': [],
    'plus': []
}

# ============================================================
# 🏅 توابع رتبه
# ============================================================
def check_timed_rank(uid):
    """چک کردن و حذف رنک‌های منقضی شده"""
    if uid in timed_ranks:
        if datetime.now() > timed_ranks[uid]['expires']:
            old_rank = timed_ranks[uid]['rank']
            # حذف از لیست رنک
            if old_rank in ranks and uid in ranks[old_rank]:
                ranks[old_rank].remove(uid)
            del timed_ranks[uid]
            return True  # رنک منقضی شد
    return False

def get_rank(uid):
    # اول چک کن رنک زمان‌دار منقضی نشده باشه
    check_timed_rank(uid)

    if uid in ranks['owners']: return 'owner'
    if uid in ranks['admins']: return 'admin'
    if uid in ranks['legend']: return 'legend'
    if uid in ranks['vip']: return 'vip'
    if uid in ranks['premium']: return 'premium'
    if uid in ranks['plus']: return 'plus'
    return 'user'

def get_rank_name(uid):
    names = {
        'owner': '👑 مالک', 'admin': '⚔️ ادمین', 'legend': '🔮 افسانه',
        'vip': '💎 ویژه', 'premium': '💜 پریمیوم', 'plus': '⭐ پلاس', 'user': '👤 کاربر'
    }
    return names.get(get_rank(uid), '👤 کاربر')

def get_rank_emoji(uid):
    emojis = {
        'owner': '👑', 'admin': '⚔️', 'legend': '🔮',
        'vip': '💎', 'premium': '💜', 'plus': '⭐', 'user': '👤'
    }
    return emojis.get(get_rank(uid), '👤')

def is_owner(uid):
    return uid in ranks['owners']

def is_admin_rank(uid):
    return uid in ranks['owners'] or uid in ranks['admins']

def is_legend(uid):
    return uid in ranks['legend'] or is_admin_rank(uid)

def is_vip(uid):
    return uid in ranks['vip'] or is_legend(uid)

def is_premium(uid):
    return uid in ranks['premium'] or is_vip(uid)

def is_plus(uid):
    return uid in ranks['plus'] or is_premium(uid)

def can_use_ai(uid):
    # 🆕 همه میتونن از AI استفاده کنن
    return True

def get_point_multiplier(uid):
    multipliers = {
        'owner': 3.0, 'admin': 2.5, 'legend': 2.0,
        'vip': 1.5, 'premium': 1.3, 'plus': 1.1, 'user': 1.0
    }
    return multipliers.get(get_rank(uid), 1.0)

# ============================================================
# 🤖 توابع دسترسی به مدل‌های AI
# ============================================================
def can_use_model(uid, model_num):
    """چک دسترسی کاربر به یک مدل خاص"""
    rank = get_rank(uid)
    user_level = RANK_LEVELS.get(rank, 1)
    model = AI_MODELS.get(model_num)
    if not model:
        return False
    model_min_level = RANK_LEVELS.get(model['min_rank'], 99)
    return user_level >= model_min_level

def get_available_models(uid):
    """لیست مدل‌های در دسترس کاربر"""
    models = []
    for num, model in AI_MODELS.items():
        if can_use_model(uid, num):
            models.append((num, model))
    return models

def get_user_model(uid):
    """گرفتن مدل انتخاب شده یا بهترین مدل پیش‌فرض"""
    if uid in user_selected_model:
        model_num = user_selected_model[uid]
        if can_use_model(uid, model_num):
            return AI_MODELS[model_num]

    # برگردون بهترین مدل در دسترس
    available = get_available_models(uid)
    if available:
        return available[0][1]
    return AI_MODELS[7]  # مدل پیش‌فرض برای همه

def get_best_free_model():
    """گرفتن بهترین مدل رایگان"""
    return AI_MODELS[7]

# ============================================================
# 👥 سیستم دعوت
# ============================================================
def get_invite_link(uid):
    """ساخت لینک دعوت کاربر"""
    return f"https://t.me/{bot.get_me().username}?start=invite_{uid}"

def add_invite(inviter_id, invited_id):
    """اضافه کردن دعوت و چک جایزه"""
    if inviter_id not in user_invites:
        user_invites[inviter_id] = {'count': 0, 'invited_users': []}

    # چک کن قبلاً این یوزر دعوت نشده باشه
    if invited_id in user_invites[inviter_id]['invited_users']:
        return None

    user_invites[inviter_id]['invited_users'].append(invited_id)
    user_invites[inviter_id]['count'] += 1

    count = user_invites[inviter_id]['count']

    # چک جایزه
    if count in INVITE_REWARDS:
        reward = INVITE_REWARDS[count]
        give_timed_rank(inviter_id, reward['rank'], reward['days'])
        return reward

    return None

def give_timed_rank(uid, rank_name, days):
    """دادن رنک زمان‌دار"""
    expires = datetime.now() + timedelta(days=days)

    # حذف از رنک‌های قبلی
    for r in ['plus', 'premium', 'vip', 'legend']:
        if uid in ranks[r]:
            ranks[r].remove(uid)

    # اضافه به رنک جدید
    if rank_name in ranks and uid not in ranks[rank_name]:
        ranks[rank_name].append(uid)

    # ذخیره تاریخ انقضا
    timed_ranks[uid] = {
        'rank': rank_name,
        'expires': expires
    }

def get_invite_count(uid):
    """تعداد دعوت‌های کاربر"""
    if uid in user_invites:
        return user_invites[uid]['count']
    return 0

def get_remaining_rank_time(uid):
    """زمان باقی‌مانده رنک"""
    if uid in timed_ranks:
        remaining = timed_ranks[uid]['expires'] - datetime.now()
        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            return f"{days} روز و {hours} ساعت"
    return None

# ============================================================
# 🔒 چک عضویت اجباری
# ============================================================
def check_membership_required(message):
    user_id = message.from_user.id

    if user_id in ranks['owners']:
        return True

    if user_id in banned_users:
        bot.reply_to(message, "🚫 شما بن شدید!")
        return False

    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        print(f"Error checking membership: {e}")

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK))
    markup.add(types.InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership"))

    bot.send_message(message.chat.id,
        f"🔒 **{message.from_user.first_name}** عزیز!\n\n"
        "⚠️ برای استفاده از ربات **باید** عضو کانال بشی!\n\n"
        "👇 اول عضو شو، بعد دکمه «عضو شدم» رو بزن:",
        reply_markup=markup, parse_mode="Markdown")
    return False

@bot.callback_query_handler(func=lambda c: c.data == "check_membership")
def verify_membership(call):
    user_id = call.from_user.id
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            bot.answer_callback_query(call.id, "✅ عضویت تایید شد!", show_alert=True)
            bot.delete_message(call.message.chat.id, call.message.message_id)
            save_user(call.from_user)
            add_points(user_id, 5)
            bot.send_message(call.message.chat.id,
                f"✅ خوش اومدی **{call.from_user.first_name}**!\n\n👺 از منو استفاده کن:",
                reply_markup=main_menu(), parse_mode="Markdown")
        else:
            bot.answer_callback_query(call.id, "❌ هنوز عضو نشدی!", show_alert=True)
    except:
        bot.answer_callback_query(call.id, "❌ خطا! دوباره تلاش کن.", show_alert=True)

# ============================================================
# 🤖 هوش مصنوعی - نسخه اصلاح شده با Fallback
# ============================================================
def ask_ai(prompt, history=None, system_prompt=None, uid=None, model_override=None):
    """ارسال درخواست به AI با پشتیبانی از چند مدل و Fallback"""

    # لیست مدل‌های جایگزین برای Fallback
    fallback_models = [
        'llama3-8b-8192',
        'llama-3.1-8b-instant',
        'gemma2-9b-it',
        'mixtral-8x7b-32768'
    ]

    # انتخاب مدل
    model = model_override
    if not model and uid:
        model = get_user_model(uid)
    if not model:
        model = AI_MODELS[7]

    model_name = model['model']

    def try_model(m_name, m_tokens, m_temp):
        """تلاش برای ارسال درخواست به یک مدل"""
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            }

            default_system = f"""تو یه دستیار هوشمند و باحال به اسم گوجو هستی.
به فارسی روان جواب بده. کوتاه، مفید و جذاب. از ایموجی مناسب استفاده کن."""

            messages = [{"role": "system", "content": system_prompt or default_system}]

            if history:
                for h in history[-8:]:
                    messages.append({
                        "role": "user" if h['role'] == 'user' else "assistant",
                        "content": h['text']
                    })

            messages.append({"role": "user", "content": prompt})

            data = {
                "model": m_name,
                "messages": messages,
                "temperature": m_temp,
                "max_tokens": m_tokens
            }

            response = requests.post(url, json=data, headers=headers, timeout=60)

            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"], None
            else:
                return None, response.status_code

        except requests.Timeout:
            return None, "timeout"
        except Exception as e:
            print(f"AI Exception: {e}")
            return None, "error"

    # اول با مدل اصلی تلاش کن
    result, error = try_model(model_name, model['tokens'], model['temp'])
    if result:
        return result

    print(f"⚠️ Model {model_name} failed with error: {error}, trying fallbacks...")

    # اگه نشد، با مدل‌های جایگزین تلاش کن
    for fallback in fallback_models:
        if fallback != model_name:
            print(f"🔄 Trying fallback model: {fallback}")
            result, error = try_model(fallback, 512, 0.7)
            if result:
                return result

    return "❌ خطا در ارتباط با AI. لطفاً دوباره تلاش کن."

# ============================================================
# 🎨 تولید تصویر با Together.ai (FLUX)
# ============================================================
def generate_image(prompt, uid):
    """تولید تصویر با Together.ai FLUX"""
    if not is_vip(uid):
        return None, "💎 فقط VIP و بالاتر!"

    try:
        # ترجمه به انگلیسی اگه فارسی بود
        if any('\u0600' <= c <= '\u06FF' for c in prompt):
            eng = ask_ai(
                f"Translate to English for image generation (only translation, nothing else): {prompt}",
                uid=uid,
                system_prompt="Translator. Only output the English translation, no explanation."
            )
            if not eng.startswith("❌"):
                prompt = eng

        # مدل‌های مختلف بر اساس رتبه
        if is_legend(uid):
            model = "black-forest-labs/FLUX.1.1-pro"
        elif is_vip(uid):
            model = "black-forest-labs/FLUX.1-schnell-Free"
        else:
            model = "black-forest-labs/FLUX.1-schnell-Free"

        url = "https://api.together.xyz/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {TOGETHER_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "prompt": prompt.strip()[:1000],
            "width": 1024,
            "height": 1024,
            "steps": 4,
            "n": 1,
            "response_format": "b64_json"
        }

        print(f"🎨 Generating image with {model}: {prompt[:50]}...")

        response = requests.post(url, json=data, headers=headers, timeout=120)

        if response.status_code == 200:
            result = response.json()

            if 'data' in result and len(result['data']) > 0:
                img_data = result['data'][0]

                # اگه base64 برگردوند
                if 'b64_json' in img_data:
                    img_bytes = base64.b64decode(img_data['b64_json'])
                    print(f"✅ Image generated: {len(img_bytes)} bytes")
                    return img_bytes, None

                # اگه URL برگردوند
                elif 'url' in img_data:
                    img_response = requests.get(img_data['url'], timeout=60)
                    if img_response.status_code == 200:
                        print(f"✅ Image downloaded: {len(img_response.content)} bytes")
                        return img_response.content, None

            return None, "❌ تصویر تولید نشد!"

        elif response.status_code == 422:
            return None, "❌ پرامپت نامعتبر! متن ساده‌تر بنویس."
        elif response.status_code == 429:
            return None, "⏳ محدودیت! چند ثانیه صبر کن."
        elif response.status_code == 401:
            return None, "❌ مشکل احراز هویت API!"
        else:
            print(f"Image API Error: {response.status_code} - {response.text[:200]}")
            return None, f"❌ خطا (کد {response.status_code})"

    except requests.Timeout:
        return None, "⏰ تایم‌اوت! دوباره تلاش کن."
    except Exception as e:
        print(f"Image Exception: {e}")
        return None, f"❌ خطا: {str(e)[:50]}"

# ============================================================
# ⭐ سیستم امتیاز
# ============================================================
def add_points(user_id, points=1):
    if user_id not in user_points:
        user_points[user_id] = 0
        user_level[user_id] = 1

    multiplier = get_point_multiplier(user_id)
    actual_points = int(points * multiplier)
    user_points[user_id] += actual_points

    new_level = (user_points[user_id] // 100) + 1
    if new_level > user_level.get(user_id, 1):
        user_level[user_id] = new_level
        return True
    return False

def get_points(user_id):
    return user_points.get(user_id, 0)

def get_level(user_id):
    return user_level.get(user_id, 1)

def get_level_title(level):
    titles = {
        1: "🌱 تازه‌کار", 2: "🌿 آماتور", 3: "🌳 حرفه‌ای",
        4: "⭐ ستاره", 5: "🌟 سوپراستار", 6: "💫 افسانه",
        7: "👑 اسطوره", 8: "🔥 خدا", 9: "💎 الماس", 10: "🏆 قهرمان"
    }
    return titles.get(min(level, 10), "🏆 قهرمان")

# ============================================================
# 🔘 دکمه‌های کمکی
# ============================================================
def close_btn():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))
    return markup

@bot.callback_query_handler(func=lambda c: c.data == "close_msg")
def close_message(call):
    try:
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
        bot.answer_callback_query(call.id, "❌")

# ============================================================
# 🛠 توابع کمکی
# ============================================================
def is_group_admin(chat_id, user_id):
    """چک ادمین بودن در گروه تلگرام"""
    try:
        member = bot.get_chat_member(chat_id, user_id)
        return member.status in ['administrator', 'creator']
    except Exception as e:
        print(f"Admin check error: {e}")
        return False

def bot_is_admin(chat_id):
    """چک ادمین بودن بات در گروه"""
    try:
        bot_member = bot.get_chat_member(chat_id, bot.get_me().id)
        return bot_member.status == 'administrator'
    except:
        return False

def save_user(user):
    users[user.id] = {
        'name': user.first_name,
        'username': user.username or '',
        'time': str(datetime.now())
    }
    if user.id not in user_points:
        user_points[user.id] = 0
        user_level[user.id] = 1

def check_cooldown(user_id, seconds=3):
    if is_premium(user_id):
        return True

    now = time.time()
    if user_id in cooldowns and now - cooldowns[user_id] < seconds:
        return False
    cooldowns[user_id] = now
    return True

def close_ai_session(user_id):
    ai_chat_users.discard(user_id)
    chat_histories.pop(user_id, None)
    ai_last_active.pop(user_id, None)
    ai_context.pop(user_id, None)

def get_uid_from_message(message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id, message.reply_to_message.from_user.first_name
    args = message.text.split()
    if len(args) >= 2:
        try:
            return int(args[1]), str(args[1])
        except:
            pass
    return None, None

def generate_whisper_code():
    return hashlib.md5(str(time.time()).encode()).hexdigest()[:8]

def generate_gift_code(length=8):
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# ============================================================
# 📱 منوها
# ============================================================
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("🎮 بازی‌ها"),
        types.KeyboardButton("🤖 هوش مصنوعی"),
        types.KeyboardButton("💌 نجوا"),
        types.KeyboardButton("🤫 اعتراف"),
        types.KeyboardButton("✨ ابزارها"),
        types.KeyboardButton("🎁 کد هدیه"),
        types.KeyboardButton("👥 دعوت"),
        types.KeyboardButton("📊 پروفایل"),
        types.KeyboardButton("📋 راهنما")
    )
    return markup

def games_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add("🎲 تاس", "🪙 سکه", "😇 حقیقت")
    markup.add("😈 جرات", "🧩 معما", "🎯 کوییز")
    markup.add("😂 جوک", "🔙 بازگشت")
    return markup

def ai_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("💬 چت AI", "🔄 تغییر مدل")
    markup.add("🎨 تصویر", "📝 داستان")
    markup.add("📜 شعر", "💻 کد")
    markup.add("🌐 ترجمه", "🔮 طالع")
    markup.add("🔙 بازگشت")
    return markup

def tools_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📝 کپشن", "📄 بیو")
    markup.add("🏷 هشتگ", "💝 تعریف")
    markup.add("🎭 رُست", "💪 انگیزشی")
    markup.add("🔙 بازگشت")
    return markup

MENU_BUTTONS = [
    "🎮 بازی‌ها", "🤖 هوش مصنوعی", "💌 نجوا", "🤫 اعتراف",
    "✨ ابزارها", "🎁 کد هدیه", "📊 پروفایل", "📋 راهنما", "🔙 بازگشت",
    "👥 دعوت",
    "🎲 تاس", "🪙 سکه", "😇 حقیقت", "😈 جرات", "🧩 معما", "🎯 کوییز", "😂 جوک",
    "💬 چت AI", "🔄 تغییر مدل", "🎨 تصویر", "📝 داستان", "📜 شعر", "💻 کد", "🌐 ترجمه", "🔮 طالع",
    "📝 کپشن", "📄 بیو", "🏷 هشتگ", "💝 تعریف", "🎭 رُست", "💪 انگیزشی"
]

# ============================================================
# 🚀 استارت
# ============================================================
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user

    # چک پارامتر
    if len(message.text.split()) > 1:
        param = message.text.split()[1]

        # 🆕 چک لینک دعوت
        if param.startswith("invite_"):
            try:
                inviter_id = int(param.replace("invite_", ""))
                if inviter_id != user.id:  # نمیتونی خودت رو دعوت کنی
                    if not check_membership_required(message):
                        return

                    reward = add_invite(inviter_id, user.id)

                    if reward:
                        # پیام به دعوت‌کننده
                        try:
                            bot.send_message(inviter_id,
                                f"🎉 **تبریک!**\n\n"
                                f"👤 {user.first_name} با لینک تو عضو شد!\n"
                                f"🎁 جایزه: {reward['name']} برای {reward['days']} روز!\n"
                                f"📊 کل دعوت‌ها: {get_invite_count(inviter_id)}",
                                parse_mode="Markdown")
                        except:
                            pass
                    else:
                        # فقط اعلام دعوت
                        try:
                            bot.send_message(inviter_id,
                                f"👤 **{user.first_name}** با لینک تو عضو شد!\n"
                                f"📊 کل دعوت‌ها: {get_invite_count(inviter_id)}",
                                parse_mode="Markdown")
                        except:
                            pass
            except:
                pass

        elif param.startswith("gift_"):
            code = param.replace("gift_", "")
            if code in gift_codes:
                if not check_membership_required(message):
                    return
                message.text = f"/redeem {code}"
                redeem_code(message)
                return

        elif param.startswith("whisper_"):
            code = param.replace("whisper_", "")
            if code in whisper_data:
                w = whisper_data[code]
                if w['to_id'] == user.id or w['to_id'] == 0:
                    bot.send_message(message.chat.id,
                        f"💌 **نجوای ناشناس:**\n\n{w['message']}\n\n👁 فقط تو میبینی!",
                        parse_mode="Markdown", reply_markup=close_btn())
                    w['seen'] = True
                    return

    if not check_membership_required(message):
        return

    save_user(user)
    add_points(user.id, 5)

    lvl = get_level(user.id)
    models = get_available_models(user.id)
    model_info = ""
    if models:
        current = get_user_model(user.id)
        model_info = f"\n🤖 مدل فعال: {current['name']}\n📊 تعداد مدل‌ها: {len(models)}"

    # نمایش زمان باقی‌مانده رنک
    remaining = get_remaining_rank_time(user.id)
    rank_info = ""
    if remaining:
        rank_info = f"\n⏰ رنک: {remaining} مانده"

    bot.send_message(message.chat.id,
        f"👋 سلام **{user.first_name}**!\n"
        f"🏅 {get_rank_name(user.id)} | {get_level_title(lvl)}"
        f"{model_info}{rank_info}\n\n"
        "👺 **گوجو v7.3**\n\n"
        "🆕 AI برای همه | ریپلای روی جواب | انتخاب مدل\n\n"
        "📋 از منو استفاده کن!",
        reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(commands=['cancel'])
def cancel_cmd(message):
    user_states.pop(message.from_user.id, None)
    close_ai_session(message.from_user.id)
    bot.reply_to(message, "❌ لغو شد", reply_markup=main_menu())

# ============================================================
# 👥 سیستم دعوت
# ============================================================
@bot.message_handler(commands=['invite', 'ref', 'referral'])
def invite_cmd(message):
    if not check_membership_required(message):
        return

    uid = message.from_user.id
    invite_link = get_invite_link(uid)
    invite_count = get_invite_count(uid)

    # محاسبه تا جایزه بعدی
    next_reward = None
    for count, reward in sorted(INVITE_REWARDS.items()):
        if invite_count < count:
            next_reward = (count, reward)
            break

    next_info = ""
    if next_reward:
        remaining = next_reward[0] - invite_count
        next_info = f"\n\n🎯 **{remaining}** دعوت تا {next_reward[1]['name']}"

    # نمایش زمان باقی‌مانده رنک
    remaining_time = get_remaining_rank_time(uid)
    time_info = ""
    if remaining_time:
        time_info = f"\n⏰ رنک فعلی: {remaining_time} مانده"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 اشتراک لینک",
        url=f"https://t.me/share/url?url={invite_link}&text=🎮 بیا تو ربات گوجو! هوش مصنوعی رایگان + کلی امکانات باحال"))
    markup.add(types.InlineKeyboardButton("🏆 جوایز دعوت", callback_data="invite_rewards"))
    markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

    bot.send_message(message.chat.id,
        f"👥 **سیستم دعوت**\n\n"
        f"🔗 لینک دعوت شما:\n`{invite_link}`\n\n"
        f"📊 دعوت‌های شما: **{invite_count}**"
        f"{next_info}{time_info}\n\n"
        f"💡 با دعوت دوستان، رنک ۱۵ روزه بگیر!",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "invite_rewards")
def show_invite_rewards(call):
    uid = call.from_user.id
    invite_count = get_invite_count(uid)

    text = "🏆 **جوایز دعوت**\n\n"

    for count, reward in sorted(INVITE_REWARDS.items()):
        if invite_count >= count:
            status = "✅"
        else:
            status = "⏳"
        text += f"{status} **{count}** دعوت ➜ {reward['name']} ({reward['days']} روز)\n"

    text += f"\n📊 دعوت‌های شما: **{invite_count}**"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_invite"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_invite")
def back_to_invite(call):
    uid = call.from_user.id
    invite_link = get_invite_link(uid)
    invite_count = get_invite_count(uid)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 اشتراک لینک",
        url=f"https://t.me/share/url?url={invite_link}&text=🎮 بیا تو ربات گوجو!"))
    markup.add(types.InlineKeyboardButton("🏆 جوایز دعوت", callback_data="invite_rewards"))
    markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

    bot.edit_message_text(
        f"👥 **سیستم دعوت**\n\n"
        f"🔗 لینک: `{invite_link}`\n\n"
        f"📊 دعوت‌ها: **{invite_count}**",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=markup)

# ============================================================
# 📱 هندلر دکمه‌های منو
# ============================================================
@bot.message_handler(func=lambda m: m.text in MENU_BUTTONS and m.chat.type == "private")
def menu_buttons_handler(message):
    if not check_membership_required(message):
        return

    text = message.text
    uid = message.from_user.id

    # دکمه بازگشت
    if text == "🔙 بازگشت":
        user_states.pop(uid, None)
        close_ai_session(uid)
        bot.send_message(message.chat.id, "👺 منوی اصلی:", reply_markup=main_menu())
        return

    # منوی اصلی
    if text == "🎮 بازی‌ها":
        bot.send_message(message.chat.id, "🎮 یه بازی انتخاب کن:", reply_markup=games_menu())

    elif text == "🤖 هوش مصنوعی":
        models = get_available_models(uid)
        current = get_user_model(uid)

        bot.send_message(message.chat.id,
            f"🤖 **هوش مصنوعی**\n\n"
            f"🎯 مدل فعال: {current['name']}\n"
            f"📊 مدل‌های شما: {len(models)}\n\n"
            f"💡 همه میتونن از AI استفاده کنن!\n"
            f"🆙 با دعوت دوستان، مدل‌های بهتر بگیر!",
            parse_mode="Markdown", reply_markup=ai_menu())

    elif text == "💌 نجوا":
        whisper_menu(message)

    elif text == "🤫 اعتراف":
        confession_menu(message)

    elif text == "✨ ابزارها":
        bot.send_message(message.chat.id, "✨ یه ابزار انتخاب کن:", reply_markup=tools_menu())

    elif text == "🎁 کد هدیه":
        gift_menu(message)

    elif text == "👥 دعوت":
        invite_cmd(message)

    elif text == "📊 پروفایل":
        profile_cmd(message)

    elif text == "📋 راهنما":
        help_menu(message)

    # بازی‌ها
    elif text == "🎲 تاس":
        bot.send_dice(message.chat.id)
        add_points(uid, 1)

    elif text == "🪙 سکه":
        result = random.choice(['🦁 شیر!', '🪙 خط!'])
        bot.reply_to(message, f"🪙 نتیجه: {result}")
        add_points(uid, 1)

    elif text == "😇 حقیقت":
        truths = [
            "بزرگترین رازت چیه؟ 🤫",
            "کراشت کیه؟ 💕",
            "از چی میترسی؟ 😨",
            "آخرین دروغت چی بود؟ 🤥",
            "اگه یه روز زندگی کنی چیکار میکنی؟ 🌟"
        ]
        bot.reply_to(message, f"😇 حقیقت:\n\n{random.choice(truths)}")
        add_points(uid, 1)

    elif text == "😈 جرات":
        dares = [
            "یه ویس بخون و بفرست! 🎤",
            "یه سلفی بفرست! 📸",
            "به کراشت پیام بده 💕",
            "استوری بذار با متن عجیب! 📱",
            "به یکی زنگ بزن بگو دوستش داری! 📞"
        ]
        bot.reply_to(message, f"😈 جرات:\n\n{random.choice(dares)}")
        add_points(uid, 1)

    elif text == "🧩 معما":
        riddle_cmd(message)

    elif text == "🎯 کوییز":
        quiz_cmd(message)

    elif text == "😂 جوک":
        jokes = [
            "😂 چرا ماهی تلفن نداره؟ چون آب خط نداره!",
            "😂 چرا کلاغ سیاهه؟ چون حموم نمیره!",
            "😂 چرا مورچه‌ها خسته نمیشن؟ چون شیش تا پا دارن!",
            "😂 برنامه‌نویس چرا عینک میزنه؟ چون C# نداره!",
            "😂 چرا کامپیوتر سرما نمیخوره؟ چون ویندوز داره!"
        ]
        bot.reply_to(message, random.choice(jokes))
        add_points(uid, 1)

    # AI
    elif text == "💬 چت AI":
        ai_chat_users.add(uid)
        chat_histories[uid] = []
        ai_last_active[uid] = time.time()

        model = get_user_model(uid)

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 تغییر مدل", callback_data="change_model_chat"))
        markup.add(types.InlineKeyboardButton("❌ خروج از چت", callback_data="close_ai"))
        bot.send_message(message.chat.id,
            f"💬 **چت با گوجو فعال شد!**\n\n"
            f"🤖 مدل: {model['name']}\n"
            f"📊 توکن: {model['tokens']}\n\n"
            "سوالت رو بپرس...\n"
            "برای خروج دکمه پایین رو بزن یا /cancel بنویس",
            parse_mode="Markdown", reply_markup=markup)

    elif text == "🔄 تغییر مدل":
        show_model_selection(message.chat.id, uid)

    elif text == "🎨 تصویر":
        if not is_vip(uid):
            bot.send_message(message.chat.id,
                "🎨 **تصویرسازی AI (FLUX)**\n\n"
                "💎 این قابلیت فقط برای **VIP** و بالاتره!\n\n"
                "🎁 با کد هدیه یا دعوت ۱۵ نفر VIP بگیر!",
                parse_mode="Markdown", reply_markup=close_btn())
            return

        model_name = "FLUX Pro" if is_legend(uid) else "FLUX Schnell"
        bot.send_message(message.chat.id,
            f"🎨 **تصویرسازی AI**\n\n"
            f"🤖 مدل: {model_name}\n\n"
            "بنویس چی میخوای بسازم:\n"
            "`/img توضیح تصویر`\n\n"
            "💡 فارسی هم قبوله (خودکار ترجمه میشه)!\n\n"
            "مثال:\n"
            "`/img یک گربه بامزه در فضا`\n"
            "`/img a beautiful sunset over mountains`\n"
            "`/img anime girl with blue hair`",
            parse_mode="Markdown")

    elif text == "📝 داستان":
        if not is_vip(uid):
            bot.reply_to(message, "💎 فقط VIP و بالاتر! با دعوت ۱۵ نفر VIP بگیر!")
            return
        bot.send_message(message.chat.id,
            "📝 **داستان‌نویسی**\n\n`/story موضوع`\n\nمثال: `/story ماجراجویی در جنگل`",
            parse_mode="Markdown")

    elif text == "📜 شعر":
        bot.send_message(message.chat.id,
            "📜 **شعر**\n\n`/poem موضوع`\n\nمثال: `/poem عشق`",
            parse_mode="Markdown")

    elif text == "💻 کد":
        if not is_vip(uid):
            bot.send_message(message.chat.id,
                "💎 کدنویسی فقط برای **VIP** و بالاتره!\n\n🎁 با دعوت ۱۵ نفر VIP بگیر!",
                parse_mode="Markdown", reply_markup=close_btn())
            return
        bot.send_message(message.chat.id,
            "💻 **کدنویسی AI**\n\n"
            "بنویس:\n`/code توضیح کد`\n\n"
            "مثال:\n"
            "`/code ماشین حساب پایتون`\n"
            "`/code تابع مرتب سازی جاوااسکریپت`",
            parse_mode="Markdown")

    elif text == "🌐 ترجمه":
        bot.send_message(message.chat.id,
            "🌐 **ترجمه**\n\n`/translate متن`\n\nمثال: `/translate سلام دنیا`",
            parse_mode="Markdown")

    elif text == "🔮 طالع":
        bot.send_message(message.chat.id,
            "🔮 **طالع‌بینی**\n\n`/horoscope ماه تولد`\n\nمثال: `/horoscope فروردین`",
            parse_mode="Markdown")

    # ابزارها
    elif text == "📝 کپشن":
        bot.send_message(message.chat.id, "📝 **کپشن‌ساز**\n\n`/caption موضوع`", parse_mode="Markdown")

    elif text == "📄 بیو":
        bot.send_message(message.chat.id, "📄 **بیوساز**\n\n`/bio سبک`", parse_mode="Markdown")

    elif text == "🏷 هشتگ":
        bot.send_message(message.chat.id, "🏷 **هشتگ‌ساز**\n\n`/hashtag موضوع`", parse_mode="Markdown")

    elif text == "💝 تعریف":
        compliment_cmd(message)

    elif text == "🎭 رُست":
        roast_cmd(message)

    elif text == "💪 انگیزشی":
        motivation_cmd(message)

# ============================================================
# 🔄 نمایش و انتخاب مدل - اصلاح شده
# ============================================================
def show_model_selection(chat_id, uid, include_ask=False):
    """نمایش دکمه‌های انتخاب مدل"""
    models = get_available_models(uid)
    current = get_user_model(uid)

    if not models:
        bot.send_message(chat_id, "❌ هیچ مدلی در دسترس نیست!")
        return

    markup = types.InlineKeyboardMarkup(row_width=1)
    for num, model in models:
        check = "✅ " if model['id'] == current['id'] else ""
        lock = ""
        if not can_use_model(uid, num):
            lock = "🔒 "
        markup.add(types.InlineKeyboardButton(
            f"{check}{lock}{model['name']} ({model['tokens']} توکن)",
            callback_data=f"select_model_{num}"
        ))

    # نمایش مدل‌های قفل شده
    all_models = list(AI_MODELS.items())
    locked_text = ""
    locked_count = 0
    for num, model in all_models:
        if not can_use_model(uid, num):
            locked_count += 1

    if locked_count > 0:
        locked_text = f"\n\n🔒 {locked_count} مدل دیگه با ارتقاء رنک باز میشه!"

    markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

    bot.send_message(chat_id,
        f"🔄 **انتخاب مدل AI**\n\n"
        f"📊 مدل‌های در دسترس: {len(models)}\n"
        f"🎯 مدل فعلی: {current['name']}\n"
        f"🏅 رنک شما: {get_rank_name(uid)}"
        f"{locked_text}\n\n"
        f"یکی انتخاب کن:",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "change_model_chat")
def change_model_in_chat(call):
    show_model_selection(call.message.chat.id, call.from_user.id)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda c: c.data.startswith("select_model_"))
def select_model_callback(call):
    try:
        model_num = int(call.data.replace("select_model_", ""))
        uid = call.from_user.id

        if not can_use_model(uid, model_num):
            model = AI_MODELS.get(model_num)
            min_rank = model['min_rank'] if model else 'unknown'
            rank_names = {
                'owner': '👑 مالک', 'admin': '⚔️ ادمین', 'legend': '🔮 افسانه',
                'vip': '💎 ویژه', 'premium': '💜 پریمیوم', 'plus': '⭐ پلاس'
            }
            bot.answer_callback_query(call.id,
                f"🔒 این مدل نیاز به رنک {rank_names.get(min_rank, min_rank)} داره!",
                show_alert=True)
            return

        user_selected_model[uid] = model_num
        model = AI_MODELS[model_num]

        bot.answer_callback_query(call.id, f"✅ {model['name']} فعال شد!", show_alert=True)

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        bot.send_message(call.message.chat.id,
            f"✅ **مدل انتخاب شد!**\n\n"
            f"🤖 مدل: {model['name']}\n"
            f"📊 توکن: {model['tokens']}\n\n"
            f"حالا میتونی از AI استفاده کنی!",
            parse_mode="Markdown", reply_markup=close_btn())
    except Exception as e:
        print(f"Model select error: {e}")
        bot.answer_callback_query(call.id, "❌ خطا!", show_alert=True)

# ============================================================
# 🤖 دستورات AI - با انتخاب مدل
# ============================================================
@bot.message_handler(commands=['ai', 'ask'])
def ai_cmd(message):
    if not check_membership_required(message):
        return

    uid = message.from_user.id
    args = message.text.split(maxsplit=1)

    # اگه فقط /ai نوشته شده، منوی انتخاب مدل رو نشون بده
    if len(args) < 2:
        models = get_available_models(uid)
        current = get_user_model(uid)

        markup = types.InlineKeyboardMarkup(row_width=1)

        # دکمه‌های مدل
        for num, model in models:
            check = "✅ " if model['id'] == current['id'] else ""
            markup.add(types.InlineKeyboardButton(
                f"{check}{model['name']}",
                callback_data=f"ai_select_{num}"
            ))

        # نمایش مدل‌های قفل
        locked_models = []
        for num, model in AI_MODELS.items():
            if not can_use_model(uid, num):
                locked_models.append(model)

        locked_text = ""
        if locked_models:
            locked_text = f"\n\n🔒 **مدل‌های قفل شده:** {len(locked_models)}\n"
            locked_text += "با ارتقاء رنک باز میشن!"

        markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

        bot.send_message(message.chat.id,
            f"🤖 **هوش مصنوعی گوجو**\n\n"
            f"🎯 مدل فعال: {current['name']}\n"
            f"🏅 رنک شما: {get_rank_name(uid)}\n"
            f"📊 مدل‌های شما: {len(models)}"
            f"{locked_text}\n\n"
            f"📝 **نحوه استفاده:**\n"
            f"`/ai سوال شما`\n\n"
            f"💡 یا یه مدل انتخاب کن و بعد سوال بپرس:",
            parse_mode="Markdown", reply_markup=markup)
        return

    if not check_cooldown(message.from_user.id, 3):
        bot.reply_to(message, "⏳ صبر کن...")
        return

    model = get_user_model(uid)

    # گرفتن تاریخچه اگر وجود داشت
    history = chat_histories.get(uid, [])

    msg = bot.send_message(message.chat.id, f"{model['name'].split()[0]} در حال فکر کردن...")
    response = ask_ai(args[1], history=history, uid=uid)

    # ذخیره تاریخچه
    if uid not in chat_histories:
        chat_histories[uid] = []
    chat_histories[uid].append({"role": "user", "text": args[1]})
    chat_histories[uid].append({"role": "assistant", "text": response})
    chat_histories[uid] = chat_histories[uid][-20:]  # نگه داشتن ۲۰ پیام آخر

    # 🆕 ذخیره context برای ریپلای
    ai_context[uid] = {
        'last_msg_id': msg.message_id,
        'model': model
    }

    # دکمه‌های پاسخ
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 مدل دیگه", callback_data="change_model_inline"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )

    try:
        bot.edit_message_text(
            f"🤖 {model['name']}\n\n{response}",
            message.chat.id, msg.message_id,
            reply_markup=markup
        )
        ai_last_message[uid] = msg.message_id
    except:
        sent = bot.send_message(
            message.chat.id,
            f"🤖 {model['name']}\n\n{response}",
            reply_markup=markup
        )
        ai_last_message[uid] = sent.message_id

    add_points(uid, 2)

@bot.callback_query_handler(func=lambda c: c.data.startswith("ai_select_"))
def ai_select_model(call):
    """انتخاب مدل از منوی /ai"""
    try:
        model_num = int(call.data.replace("ai_select_", ""))
        uid = call.from_user.id

        if not can_use_model(uid, model_num):
            model = AI_MODELS.get(model_num)
            min_rank = model['min_rank'] if model else 'unknown'
            rank_names = {
                'owner': '👑 مالک', 'admin': '⚔️ ادمین', 'legend': '🔮 افسانه',
                'vip': '💎 ویژه', 'premium': '💜 پریمیوم', 'plus': '⭐ پلاس'
            }
            bot.answer_callback_query(call.id,
                f"🔒 نیاز به رنک {rank_names.get(min_rank, min_rank)}!",
                show_alert=True)
            return

        user_selected_model[uid] = model_num
        model = AI_MODELS[model_num]

        bot.answer_callback_query(call.id, f"✅ {model['name']} فعال شد!")

        # آپدیت پیام
        models = get_available_models(uid)
        markup = types.InlineKeyboardMarkup(row_width=1)

        for num, m in models:
            check = "✅ " if m['id'] == model['id'] else ""
            markup.add(types.InlineKeyboardButton(
                f"{check}{m['name']}",
                callback_data=f"ai_select_{num}"
            ))

        markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

        try:
            bot.edit_message_text(
                f"🤖 **مدل انتخاب شد!**\n\n"
                f"✅ مدل فعال: {model['name']}\n"
                f"📊 توکن: {model['tokens']}\n\n"
                f"📝 حالا بنویس:\n`/ai سوال شما`",
                call.message.chat.id, call.message.message_id,
                parse_mode="Markdown", reply_markup=markup
            )
        except:
            pass

    except Exception as e:
        print(f"AI select error: {e}")
        bot.answer_callback_query(call.id, "❌ خطا!")

@bot.callback_query_handler(func=lambda c: c.data == "change_model_inline")
def change_model_inline(call):
    """تغییر مدل از پاسخ AI"""
    uid = call.from_user.id
    models = get_available_models(uid)
    current = get_user_model(uid)

    markup = types.InlineKeyboardMarkup(row_width=1)
    for num, model in models:
        check = "✅ " if model['id'] == current['id'] else ""
        markup.add(types.InlineKeyboardButton(
            f"{check}{model['name']}",
            callback_data=f"select_model_{num}"
        ))
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="close_msg"))

    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id,
        f"🔄 **انتخاب مدل**\n\n"
        f"🎯 فعلی: {current['name']}\n"
        f"🏅 رنک: {get_rank_name(uid)}",
        parse_mode="Markdown", reply_markup=markup)

# ============================================================
# 🆕 هندلر ریپلای روی پاسخ AI - اصلاح شده
# ============================================================
@bot.message_handler(func=lambda m: m.reply_to_message is not None and m.chat.type == "private" and not m.text.startswith('/') and m.text not in MENU_BUTTONS)
def reply_ai_handler(message):
    """هندلر ریپلای روی پیام‌های بات"""
    uid = message.from_user.id

    # چک کن که آیا ریپلای به پیام بات هست
    if not message.reply_to_message.from_user:
        return

    if message.reply_to_message.from_user.id != bot.get_me().id:
        return

    # چک متن پیام بات - باید حاوی پاسخ AI باشه
    reply_text = message.reply_to_message.text or ""
    if not (reply_text.startswith("🤖") or "در حال فکر" in reply_text or uid in ai_context or uid in ai_chat_users):
        return

    if not check_membership_required(message):
        return

    if not check_cooldown(uid, 3):
        bot.reply_to(message, "⏳ صبر کن...")
        return

    model = get_user_model(uid)
    history = chat_histories.get(uid, [])

    msg = bot.send_message(message.chat.id, f"{model['name'].split()[0]} در حال فکر کردن...")
    response = ask_ai(message.text, history=history, uid=uid)

    # آپدیت تاریخچه
    if uid not in chat_histories:
        chat_histories[uid] = []
    chat_histories[uid].append({"role": "user", "text": message.text})
    chat_histories[uid].append({"role": "assistant", "text": response})
    chat_histories[uid] = chat_histories[uid][-20:]

    # آپدیت context
    ai_context[uid] = {
        'last_msg_id': msg.message_id,
        'model': model
    }

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🔄 مدل دیگه", callback_data="change_model_inline"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )

    try:
        bot.edit_message_text(
            f"🤖 {model['name']}\n\n{response}",
            message.chat.id, msg.message_id,
            reply_markup=markup
        )
        ai_last_message[uid] = msg.message_id
    except:
        sent = bot.send_message(
            message.chat.id,
            f"🤖 {model['name']}\n\n{response}",
            reply_markup=markup
        )
        ai_last_message[uid] = sent.message_id

    add_points(uid, 2)

# ============================================================
# 🎁 سیستم کد هدیه
# ============================================================
def gift_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 وارد کردن کد", callback_data="enter_gift_code"),
        types.InlineKeyboardButton("🏆 رتبه‌ها", callback_data="show_ranks"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )

    bot.send_message(message.chat.id,
        "🎁 **کد هدیه**\n\n"
        "اگه کد هدیه داری، اینجا فعالش کن!\n\n"
        "📝 یا دستور:\n`/redeem کد`",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "enter_gift_code")
def enter_gift_code(call):
    user_states[call.from_user.id] = {'state': 'waiting_gift_code'}
    bot.edit_message_text(
        "🎁 **کدت رو بنویس:**\n\n❌ برای لغو: /cancel",
        call.message.chat.id, call.message.message_id, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda c: c.data == "show_ranks")
def show_ranks_info(call):
    text = """🏆 **سیستم رتبه‌ها و مدل‌ها:**

👑 **مالک** - ۷ مدل AI + 🎨 FLUX Pro
⚔️ **ادمین** - ۶ مدل AI + 🎨 FLUX Pro
🔮 **افسانه** - ۵ مدل AI + 🎨 FLUX Pro
💎 **ویژه** - ۴ مدل AI + 🎨 FLUX Schnell + 💻 کد
💜 **پریمیوم** - ۳ مدل AI + نامحدود
⭐ **پلاس** - ۲ مدل AI + چت
👤 **کاربر** - ۱ مدل AI (رایگان!)

📊 **جوایز دعوت (۱۵ روزه):**
• ۳ دعوت ➜ ⭐ پلاس
• ۷ دعوت ➜ 💜 پریمیوم
• ۱۵ دعوت ➜ 💎 ویژه
• ۳۰ دعوت ➜ 🔮 افسانه

🎨 تصویرسازی با FLUX (VIP+)
💡 با دعوت یا کد هدیه رتبه بگیر!"""

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="back_to_gift"))

    bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "back_to_gift")
def back_to_gift(call):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 وارد کردن کد", callback_data="enter_gift_code"),
        types.InlineKeyboardButton("🏆 رتبه‌ها", callback_data="show_ranks"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )

    bot.edit_message_text(
        "🎁 **کد هدیه**\n\n"
        "اگه کد هدیه داری، اینجا فعالش کن!\n\n"
        "📝 یا دستور:\n`/redeem کد`",
        call.message.chat.id, call.message.message_id,
        parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(commands=['giftcode', 'createcode'])
def create_gift_code(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split()

    if len(args) < 3:
        bot.reply_to(message,
            "🎁 **ساخت کد هدیه**\n\n"
            "📝 فرمت: `/giftcode نوع مقدار [تعداد] [کد]`\n\n"
            "📌 **انواع:**\n"
            "• `PLUS` ⭐ | `PREMIUM` 💜 | `VIP` 💎\n"
            "• `LEGEND` 🔮 | `ADMIN` ⚔️\n"
            "• `POINTS 100` | `LEVEL 5`\n\n"
            "📌 **مثال:**\n"
            "`/giftcode PLUS 1 10`\n"
            "`/giftcode VIP 1 5 GOJO`",
            parse_mode="Markdown", reply_markup=close_btn())
        return

    gift_type = args[1].upper()
    value = int(args[2]) if args[2].isdigit() else 1
    max_uses = int(args[3]) if len(args) > 3 and args[3].isdigit() else 1
    custom_code = args[4].upper() if len(args) > 4 else None

    valid_types = ['PLUS', 'PREMIUM', 'VIP', 'LEGEND', 'ADMIN', 'POINTS', 'LEVEL']
    if gift_type not in valid_types:
        bot.reply_to(message, f"❌ نوع نامعتبر!", reply_markup=close_btn())
        return

    code = custom_code or generate_gift_code()

    if code in gift_codes:
        bot.reply_to(message, f"❌ کد `{code}` قبلاً وجود داره!", parse_mode="Markdown")
        return

    gift_codes[code] = {
        'type': gift_type,
        'value': value,
        'max_uses': max_uses,
        'uses': 0,
        'created_by': message.from_user.id,
        'used_by': []
    }

    type_names = {
        'PLUS': '⭐ پلاس', 'PREMIUM': '💜 پریمیوم', 'VIP': '💎 ویژه',
        'LEGEND': '🔮 افسانه', 'ADMIN': '⚔️ ادمین',
        'POINTS': '🪙 امتیاز', 'LEVEL': '📊 لول'
    }

    bot.reply_to(message,
        f"✅ **کد ساخته شد!**\n\n"
        f"🎁 کد: `{code}`\n"
        f"📦 نوع: {type_names.get(gift_type)}\n"
        f"👥 تعداد: {max_uses}\n\n"
        f"🔗 `https://t.me/{bot.get_me().username}?start=gift_{code}`",
        parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['redeem', 'code', 'gift'])
def redeem_code(message):
    if not check_membership_required(message):
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "🎁 **فعال‌سازی کد**\n\n`/redeem کد`", parse_mode="Markdown")
        return

    code = args[1].upper()
    user_id = message.from_user.id

    if code not in gift_codes:
        bot.reply_to(message, "❌ کد نامعتبر!", reply_markup=close_btn())
        return

    gift = gift_codes[code]

    if user_id in gift['used_by']:
        bot.reply_to(message, "⚠️ قبلاً استفاده کردی!", reply_markup=close_btn())
        return

    if gift['uses'] >= gift['max_uses']:
        bot.reply_to(message, "❌ ظرفیت تموم شد!", reply_markup=close_btn())
        return

    gift_type = gift['type']
    value = gift['value']

    if gift_type == 'PLUS':
        if user_id not in ranks['plus']:
            ranks['plus'].append(user_id)
        reward_text = "⭐ رتبه پلاس + ۲ مدل AI"
    elif gift_type == 'PREMIUM':
        if user_id not in ranks['premium']:
            ranks['premium'].append(user_id)
        if user_id in ranks['plus']:
            ranks['plus'].remove(user_id)
        reward_text = "💜 رتبه پریمیوم + ۳ مدل AI"
    elif gift_type == 'VIP':
        if user_id not in ranks['vip']:
            ranks['vip'].append(user_id)
        for r in ['plus', 'premium']:
            if user_id in ranks[r]:
                ranks[r].remove(user_id)
        reward_text = "💎 رتبه ویژه + ۴ مدل AI + تصویر"
    elif gift_type == 'LEGEND':
        if user_id not in ranks['legend']:
            ranks['legend'].append(user_id)
        for r in ['plus', 'premium', 'vip']:
            if user_id in ranks[r]:
                ranks[r].remove(user_id)
        reward_text = "🔮 رتبه افسانه + ۵ مدل AI"
    elif gift_type == 'ADMIN':
        if user_id not in ranks['admins']:
            ranks['admins'].append(user_id)
        reward_text = "⚔️ رتبه ادمین + ۶ مدل AI"
    elif gift_type == 'POINTS':
        add_points(user_id, value)
        reward_text = f"🪙 {value} امتیاز"
    elif gift_type == 'LEVEL':
        if user_id not in user_level:
            user_level[user_id] = 1
        user_level[user_id] += value
        reward_text = f"📊 {value} لول"
    else:
        reward_text = "🎁 جایزه"

    gift['uses'] += 1
    gift['used_by'].append(user_id)

    bot.reply_to(message,
        f"🎉 **کد فعال شد!**\n\n"
        f"🎁 جایزه: {reward_text}\n"
        f"👤 {message.from_user.first_name}",
        parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['giftlist', 'codes'])
def list_gift_codes(message):
    if message.from_user.id not in ranks['owners']:
        return

    if not gift_codes:
        bot.reply_to(message, "📭 کدی نیست!", reply_markup=close_btn())
        return

    text = "🎁 **کدها:**\n\n"
    for code, data in gift_codes.items():
        status = "✅" if data['uses'] < data['max_uses'] else "❌"
        text += f"{status} `{code}` - {data['type']} ({data['uses']}/{data['max_uses']})\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['delcode'])
def delete_gift_code(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "`/delcode کد`", parse_mode="Markdown")
        return

    code = args[1].upper()
    if code in gift_codes:
        del gift_codes[code]
        bot.reply_to(message, f"✅ `{code}` حذف شد!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ کد پیدا نشد!")

# ============================================================
# 💌 نجوا
# ============================================================
def whisper_menu(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("💌 ارسال نجوا", callback_data="whisper_new"))
    markup.add(types.InlineKeyboardButton("❌ بستن", callback_data="close_msg"))

    bot.send_message(message.chat.id,
        "💌 **نجوا**\n\n"
        "پیام ناشناس بفرست!\n\n"
        "📝 در گروه:\n"
        "`/whisper @user پیام`\n"
        "`/w 123456 پیام`",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data == "whisper_new")
def whisper_new(call):
    user_states[call.from_user.id] = {'state': 'whisper_waiting_id'}
    bot.edit_message_text("💌 آیدی عددی گیرنده:\n\n/cancel برای لغو",
                         call.message.chat.id, call.message.message_id)

@bot.message_handler(commands=['whisper', 'w'])
def whisper_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=2)

    if message.reply_to_message and len(args) >= 2:
        to_user = message.reply_to_message.from_user
        text = ' '.join(args[1:])
        code = generate_whisper_code()
        whisper_data[code] = {
            'from_id': message.from_user.id,
            'to_id': to_user.id,
            'message': text,
            'seen': False
        }
        link = f"https://t.me/{bot.get_me().username}?start=whisper_{code}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💌 نجوا", url=link))
        bot.send_message(message.chat.id, f"💌 نجوا برای **{to_user.first_name}**",
                        parse_mode="Markdown", reply_markup=markup)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_points(message.from_user.id, 2)
        return

    if len(args) >= 3:
        target, text = args[1], args[2]
        code = generate_whisper_code()
        to_id = int(target) if target.isdigit() else 0
        whisper_data[code] = {
            'from_id': message.from_user.id,
            'to_id': to_id,
            'message': text,
            'seen': False
        }
        link = f"https://t.me/{bot.get_me().username}?start=whisper_{code}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("💌 نجوا", url=link))
        bot.send_message(message.chat.id, "💌 نجوا آماده!", reply_markup=markup)
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except:
            pass
        add_points(message.from_user.id, 2)
        return

    bot.reply_to(message, "💡 `/whisper @user پیام`", parse_mode="Markdown")

# ============================================================
# 🤫 اعتراف
# ============================================================
def confession_menu(message):
    bot.send_message(message.chat.id,
        "🤫 **اعتراف**\n\n"
        "اعتراف ناشناس توی گروه!\n\n"
        "📝 در گروه:\n`/confess متن`",
        parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['confess'])
def confess_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "`/confess متن`", parse_mode="Markdown")
        return

    chat_id = message.chat.id
    if chat_id not in confession_count:
        confession_count[chat_id] = 0
    confession_count[chat_id] += 1

    try:
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("❤️ 0", callback_data=f"conf_l_{confession_count[chat_id]}"),
        types.InlineKeyboardButton("😢 0", callback_data=f"conf_s_{confession_count[chat_id]}")
    )

    bot.send_message(message.chat.id,
        f"🤫 **اعتراف #{confession_count[chat_id]}**\n\n{args[1]}\n\n👤 ناشناس",
        parse_mode="Markdown", reply_markup=markup)
    add_points(message.from_user.id, 3)

@bot.callback_query_handler(func=lambda c: c.data.startswith("conf_"))
def conf_react(call):
    parts = call.data.split("_")
    reaction, conf_id = parts[1], parts[2]
    msg_id = call.message.message_id

    if msg_id not in confession_reactions:
        confession_reactions[msg_id] = {'l': 0, 's': 0, 'users': set()}

    if call.from_user.id in confession_reactions[msg_id]['users']:
        bot.answer_callback_query(call.id, "⚠️ قبلاً واکنش دادی!")
        return

    confession_reactions[msg_id]['users'].add(call.from_user.id)
    confession_reactions[msg_id][reaction] += 1

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(f"❤️ {confession_reactions[msg_id]['l']}", callback_data=f"conf_l_{conf_id}"),
        types.InlineKeyboardButton(f"😢 {confession_reactions[msg_id]['s']}", callback_data=f"conf_s_{conf_id}")
    )

    try:
        bot.edit_message_reply_markup(call.message.chat.id, msg_id, reply_markup=markup)
    except:
        pass
    bot.answer_callback_query(call.id, "✅")

# ============================================================
# 📋 راهنمای کامل بات
# ============================================================
def help_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎮 بازی", callback_data="help_games"),
        types.InlineKeyboardButton("🤖 AI", callback_data="help_ai"),
        types.InlineKeyboardButton("💌 نجوا", callback_data="help_whisper"),
        types.InlineKeyboardButton("🎁 کد", callback_data="help_gift"),
        types.InlineKeyboardButton("👥 دعوت", callback_data="help_invite"),
        types.InlineKeyboardButton("🏆 رتبه‌ها", callback_data="help_ranks"),
        types.InlineKeyboardButton("👮 مدیریت", callback_data="help_admin"),
        types.InlineKeyboardButton("📜 همه دستورات", callback_data="help_all"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )
    bot.send_message(message.chat.id, "📋 **راهنمای ربات گوجو v7.3**\n\nیه بخش انتخاب کن:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("help_"))
def help_section(call):
    section = call.data.replace("help_", "")

    texts = {
        "games": """🎮 **بازی‌ها**

🎲 **تاس** - پرتاب تاس
🪙 **سکه** - شیر یا خط
😇 **حقیقت** - سوال حقیقت
😈 **جرات** - چالش جرات
🧩 **معما** - `/riddle` - معما با جواب
🎯 **کوییز** - `/quiz موضوع` - سوال چهارگزینه‌ای
😂 **جوک** - جوک تصادفی

💡 همه میتونن بازی کنن و امتیاز بگیرن!""",

        "ai": """🤖 **هوش مصنوعی**

💬 **چت AI** - مکالمه با گوجو
🔄 **تغییر مدل** - انتخاب مدل AI

📌 **دستورات AI:**
`/ai` - نمایش مدل‌ها و انتخاب
`/ai سوال` - پرسیدن سوال
`/img توضیح` - تصویرسازی (VIP+)
`/story موضوع` - داستان (VIP+)
`/poem موضوع` - شعر
`/code توضیح` - کدنویسی (VIP+)
`/translate متن` - ترجمه
`/horoscope ماه` - طالع‌بینی

💡 **ریپلای روی پاسخ AI:**
روی جواب بات ریپلای بزن و سوال بعدی رو بپرس!

🆕 همه کاربران ۱ مدل رایگان دارن!""",

        "whisper": """💌 **نجوا و اعتراف**

**نجوا (پیام ناشناس):**
`/whisper @user پیام` - به یوزرنیم
`/w ID پیام` - به آیدی عددی

💡 روی پیام کسی ریپلای کن و `/w پیام` بنویس

**اعتراف (در گروه):**
`/confess متن` - اعتراف ناشناس

⚠️ پیامت خودکار حذف میشه!""",

        "gift": """🎁 **کد هدیه**

`/redeem کد` - فعال‌سازی کد

**انواع جوایز:**
• ⭐ پلاس - ۲ مدل AI
• 💜 پریمیوم - ۳ مدل AI + نامحدود
• 💎 ویژه - ۴ مدل AI + تصویر + کد
• 🔮 افسانه - ۵ مدل AI
• 🪙 امتیاز
• 📊 لول

💡 کد هدیه از ادمین بگیر!""",

        "invite": """👥 **سیستم دعوت**

`/invite` - دریافت لینک دعوت

**جوایز دعوت (۱۵ روزه):**
• ۳ دعوت ➜ ⭐ پلاس
• ۷ دعوت ➜ 💜 پریمیوم
• ۱۵ دعوت ➜ 💎 ویژه
• ۳۰ دعوت ➜ 🔮 افسانه

💡 لینکت رو به دوستات بفرست!
⏰ رنک‌ها ۱۵ روز اعتبار دارن""",

        "ranks": """🏆 **سیستم رتبه‌ها**

👑 **مالک** - همه امکانات + ۷ مدل
⚔️ **ادمین** - ۶ مدل AI + FLUX Pro
🔮 **افسانه** - ۵ مدل AI + FLUX Pro
💎 **ویژه** - ۴ مدل AI + FLUX + کد
💜 **پریمیوم** - ۳ مدل AI + نامحدود
⭐ **پلاس** - ۲ مدل AI
👤 **کاربر** - ۱ مدل AI رایگان

**نحوه گرفتن رتبه:**
• 🎁 کد هدیه
• 👥 دعوت دوستان (۱۵ روزه)""",

        "admin": """👮 **مدیریت گروه**

⚠️ **نیاز به ادمین بودن بات!**

`/warn` - اخطار (۳ اخطار = بن)
`/mute` - سکوت ۱ ساعته
`/unmute` - رفع سکوت
`/kick` - اخراج
`/ban` - بن دائم
`/unban` - آنبن
`/del` - حذف پیام
`/clearwarn` - پاک کردن اخطارها

💡 روی پیام کاربر ریپلای کن!""",

        "all": """📜 **همه دستورات ربات**

**🚀 عمومی:**
`/start` - شروع ربات
`/menu` - منوی اصلی
`/cancel` - لغو عملیات
`/profile` یا `/me` - پروفایل
`/top` - برترین‌ها
`/id` - آیدی کاربر
`/ping` - تست سرعت

**🤖 هوش مصنوعی:**
`/ai` - منوی AI و انتخاب مدل
`/ai سوال` - پرسیدن از AI
`/img توضیح` - تصویرسازی
`/story موضوع` - داستان
`/poem موضوع` - شعر
`/code توضیح` - کدنویسی
`/translate متن` - ترجمه
`/horoscope ماه` - طالع

**✨ ابزارها:**
`/caption موضوع` - کپشن
`/bio سبک` - بیو
`/hashtag موضوع` - هشتگ
`/roast` - رُست
`/compliment` - تعریف
`/motivation` - انگیزشی

**🎮 بازی:**
`/riddle` - معما
`/quiz موضوع` - کوییز

**💌 نجوا:**
`/whisper @user پیام`
`/w ID پیام`
`/confess متن` - اعتراف

**🎁 هدیه و دعوت:**
`/redeem کد` - فعال‌سازی
`/invite` - لینک دعوت

**👮 گروه:**
`/warn` `/mute` `/unmute`
`/kick` `/ban` `/unban`
`/del` `/clearwarn`

**👑 مالک:**
`/panel` - پنل مدیریت
`/giftcode نوع مقدار تعداد`
`/sendall پیام` - همگانی
`/addadmin` `/addvip` `/addplus`
`/banuser` `/unbanuser`
`/givepoints ID مقدار`"""
    }

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 برگشت", callback_data="help_back"))

    text = texts.get(section, "❌")

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=markup)
    except:
        bot.answer_callback_query(call.id, "❌")

@bot.callback_query_handler(func=lambda c: c.data == "help_back")
def help_back(call):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎮 بازی", callback_data="help_games"),
        types.InlineKeyboardButton("🤖 AI", callback_data="help_ai"),
        types.InlineKeyboardButton("💌 نجوا", callback_data="help_whisper"),
        types.InlineKeyboardButton("🎁 کد", callback_data="help_gift"),
        types.InlineKeyboardButton("👥 دعوت", callback_data="help_invite"),
        types.InlineKeyboardButton("🏆 رتبه‌ها", callback_data="help_ranks"),
        types.InlineKeyboardButton("👮 مدیریت", callback_data="help_admin"),
        types.InlineKeyboardButton("📜 همه دستورات", callback_data="help_all"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )
    bot.edit_message_text("📋 **راهنمای ربات گوجو v7.3**\n\nیه بخش انتخاب کن:",
                         call.message.chat.id, call.message.message_id,
                         parse_mode="Markdown", reply_markup=markup)

# ============================================================
# 📊 پروفایل
# ============================================================
@bot.message_handler(commands=['profile', 'me'])
def profile_cmd(message):
    if not check_membership_required(message):
        return

    user = message.from_user
    points = get_points(user.id)
    level = get_level(user.id)
    progress = points % 100
    bar = "▓" * (progress // 10) + "░" * (10 - progress // 10)
    multiplier = get_point_multiplier(user.id)

    models = get_available_models(user.id)
    current = get_user_model(user.id)
    invites = get_invite_count(user.id)

    model_info = f"🤖 مدل‌ها: {len(models)}" if models else "🤖 بدون AI"
    current_info = f"\n🎯 فعال: {current['name']}" if current else ""

    # زمان باقی‌مانده رنک
    remaining = get_remaining_rank_time(user.id)
    time_info = f"\n⏰ رنک: {remaining}" if remaining else ""

    bot.send_message(message.chat.id,
        f"👤 **پروفایل**\n\n"
        f"📛 {user.first_name}\n"
        f"🆔 `{user.id}`\n"
        f"🏅 {get_rank_name(user.id)}{time_info}\n"
        f"{model_info}{current_info}\n\n"
        f"⭐ امتیاز: {points}\n"
        f"📊 لول: {level} {get_level_title(level)}\n"
        f"🔥 ضریب: {multiplier}x\n"
        f"👥 دعوت‌ها: {invites}\n"
        f"[{bar}] {progress}%",
        parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['top', 'leaderboard'])
def top_cmd(message):
    if not check_membership_required(message):
        return

    if not user_points:
        bot.reply_to(message, "❌ لیست خالیه!")
        return

    sorted_users = sorted(user_points.items(), key=lambda x: x[1], reverse=True)[:10]
    text = "🏆 **برترین‌ها**\n\n"
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]

    for i, (uid, pts) in enumerate(sorted_users):
        name = users.get(uid, {}).get('name', str(uid))[:15]
        rank_emoji = get_rank_emoji(uid)
        text += f"{medals[i]} {rank_emoji} {name} - {pts}⭐\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=close_btn())

# ============================================================
# 🤖 سایر دستورات AI
# ============================================================
@bot.message_handler(commands=['img', 'image'])
def img_cmd(message):
    if not check_membership_required(message):
        return

    if not is_vip(message.from_user.id):
        bot.reply_to(message, "💎 فقط VIP و بالاتر!\n\n👥 با دعوت ۱۵ نفر VIP بگیر!", reply_markup=close_btn())
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message,
            "🎨 **تصویرسازی**\n\n"
            "`/img توضیح تصویر`\n\n"
            "مثال:\n"
            "`/img یک گربه در فضا`\n"
            "`/img sunset over mountains`",
            parse_mode="Markdown")
        return

    if not check_cooldown(message.from_user.id, 15):
        bot.reply_to(message, "⏳ ۱۵ ثانیه صبر کن!")
        return

    model_name = "FLUX Pro" if is_legend(message.from_user.id) else "FLUX Schnell"
    msg = bot.send_message(message.chat.id,
        f"🎨 **در حال تولید تصویر...**\n\n"
        f"🤖 مدل: {model_name}\n"
        "⏳ چند ثانیه صبر کن...\n"
        "💡 ترجمه خودکار فارسی فعاله")

    img, err = generate_image(args[1], message.from_user.id)

    if img:
        try:
            bot.delete_message(message.chat.id, msg.message_id)
        except:
            pass

        bot.send_photo(message.chat.id, img,
                      caption=f"🎨 **{args[1][:100]}**\n\n👤 {message.from_user.first_name}",
                      parse_mode="Markdown", reply_markup=close_btn())
        add_points(message.from_user.id, 5)
    else:
        bot.edit_message_text(err or "❌ خطا!",
                             message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['story'])
def story_cmd(message):
    if not check_membership_required(message):
        return
    if not is_vip(message.from_user.id):
        bot.reply_to(message, "💎 فقط VIP و بالاتر! با دعوت ۱۵ نفر VIP بگیر!")
        return

    args = message.text.split(maxsplit=1)
    topic = args[1] if len(args) > 1 else "ماجراجویی"

    if not check_cooldown(message.from_user.id, 10):
        bot.reply_to(message, "⏳ صبر کن...")
        return

    msg = bot.send_message(message.chat.id, "📝 در حال نوشتن...")

    response = ask_ai(
        f"یک داستان کوتاه فارسی درباره «{topic}» بنویس. ۱۵۰ کلمه.",
        system_prompt="داستان‌نویس خلاق",
        uid=message.from_user.id
    )

    bot.edit_message_text(f"📖 **{topic}**\n\n{response}",
                         message.chat.id, msg.message_id,
                         parse_mode="Markdown", reply_markup=close_btn())
    add_points(message.from_user.id, 3)

@bot.message_handler(commands=['poem'])
def poem_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    topic = args[1] if len(args) > 1 else "عشق"

    if not check_cooldown(message.from_user.id, 5):
        return

    msg = bot.send_message(message.chat.id, "📜 در حال سرودن...")
    response = ask_ai(
        f"یک شعر فارسی درباره «{topic}» بنویس. ۴-۶ بیت.",
        system_prompt="شاعر ایرانی",
        uid=message.from_user.id
    )
    bot.edit_message_text(f"📜 **{topic}**\n\n{response}",
                         message.chat.id, msg.message_id,
                         parse_mode="Markdown", reply_markup=close_btn())
    add_points(message.from_user.id, 2)

@bot.message_handler(commands=['code'])
def code_cmd(message):
    if not check_membership_required(message):
        return
    if not is_vip(message.from_user.id):
        bot.reply_to(message, "💎 فقط VIP و بالاتر! با دعوت ۱۵ نفر VIP بگیر!")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message,
            "💻 **کدنویسی AI**\n\n"
            "`/code توضیح کد`\n\n"
            "مثال:\n"
            "`/code ماشین حساب پایتون`\n"
            "`/code سورت آرایه جاوااسکریپت`",
            parse_mode="Markdown")
        return

    if not check_cooldown(message.from_user.id, 8):
        bot.reply_to(message, "⏳ صبر کن...")
        return

    msg = bot.send_message(message.chat.id, "💻 در حال کدنویسی...")

    prompt = f"""کد زیر رو بنویس:
{args[1]}

قوانین:
1. کد کامل و قابل اجرا باشه
2. کامنت فارسی داشته باشه
3. تمیز و خوانا باشه
4. اگه زبان مشخص نیست، پایتون بنویس"""

    response = ask_ai(prompt, system_prompt="برنامه‌نویس حرفه‌ای. کد تمیز با کامنت فارسی.", uid=message.from_user.id)

    if len(response) > 3900:
        response = response[:3900] + "\n\n... (کد طولانی‌تر بود)"

    try:
        bot.edit_message_text(f"💻 **کد:**\n\n{response}",
                             message.chat.id, msg.message_id,
                             reply_markup=close_btn())
    except Exception as e:
        print(f"Code error: {e}")
        bot.edit_message_text(f"💻\n\n{response[:3000]}",
                             message.chat.id, msg.message_id,
                             reply_markup=close_btn())

    add_points(message.from_user.id, 3)

@bot.message_handler(commands=['translate', 'tr'])
def translate_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "`/translate متن`", parse_mode="Markdown")
        return

    if not check_cooldown(message.from_user.id, 3):
        return

    msg = bot.send_message(message.chat.id, "🌐 در حال ترجمه...")

    text = args[1]
    if any('\u0600' <= c <= '\u06FF' for c in text):
        prompt = f"ترجمه به انگلیسی:\n{text}"
    else:
        prompt = f"ترجمه به فارسی:\n{text}"

    response = ask_ai(prompt, system_prompt="مترجم. فقط ترجمه بنویس.", uid=message.from_user.id)
    bot.edit_message_text(f"🌐 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())
    add_points(message.from_user.id, 1)

@bot.message_handler(commands=['horoscope', 'fal'])
def horoscope_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        bot.reply_to(message, "`/horoscope ماه`\n\nمثال: `/horoscope فروردین`", parse_mode="Markdown")
        return

    if not check_cooldown(message.from_user.id, 5):
        return

    msg = bot.send_message(message.chat.id, "🔮 در حال دیدن...")
    response = ask_ai(
        f"طالع امروز {args[1]}. عشق، کار، سلامت.",
        system_prompt="فالگیر",
        uid=message.from_user.id
    )
    bot.edit_message_text(f"🔮 **{args[1]}**\n\n{response}",
                         message.chat.id, msg.message_id,
                         parse_mode="Markdown", reply_markup=close_btn())
    add_points(message.from_user.id, 2)

@bot.message_handler(commands=['caption'])
def caption_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    topic = args[1] if len(args) > 1 else "زندگی"

    if not check_cooldown(message.from_user.id, 5):
        return

    msg = bot.send_message(message.chat.id, "📝 ...")
    response = ask_ai(f"۳ کپشن اینستا درباره {topic}", system_prompt="کپشن‌نویس", uid=message.from_user.id)
    bot.edit_message_text(f"📝 **{topic}**\n\n{response}",
                         message.chat.id, msg.message_id,
                         parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['bio'])
def bio_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    style = args[1] if len(args) > 1 else "باحال"

    if not check_cooldown(message.from_user.id, 5):
        return

    msg = bot.send_message(message.chat.id, "📄 ...")
    response = ask_ai(f"۳ بیو {style} برای پروفایل", system_prompt="بیونویس", uid=message.from_user.id)
    bot.edit_message_text(f"📄 **{style}**\n\n{response}",
                         message.chat.id, msg.message_id,
                         parse_mode="Markdown", reply_markup=close_btn())

@bot.message_handler(commands=['hashtag', 'tag'])
def hashtag_cmd(message):
    if not check_membership_required(message):
        return

    args = message.text.split(maxsplit=1)
    topic = args[1] if len(args) > 1 else "عمومی"

    if not check_cooldown(message.from_user.id, 3):
        return

    msg = bot.send_message(message.chat.id, "🏷 ...")
    response = ask_ai(f"۱۵ هشتگ برای {topic}", system_prompt="هشتگ‌ساز", uid=message.from_user.id)
    bot.edit_message_text(f"🏷 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['riddle'])
def riddle_cmd(message):
    if not check_membership_required(message):
        return
    if not check_cooldown(message.from_user.id, 5):
        return

    msg = bot.send_message(message.chat.id, "🧩 ...")
    response = ask_ai("یه معما با جواب", system_prompt="معماساز", uid=message.from_user.id)
    bot.edit_message_text(f"🧩 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['quiz'])
def quiz_cmd(message):
    if not check_membership_required(message):
        return
    if not check_cooldown(message.from_user.id, 5):
        return

    args = message.text.split(maxsplit=1)
    topic = args[1] if len(args) > 1 else "عمومی"

    msg = bot.send_message(message.chat.id, "🎯 ...")
    response = ask_ai(f"کوییز ۴ گزینه‌ای {topic} با جواب", system_prompt="کوییزساز", uid=message.from_user.id)
    bot.edit_message_text(f"🎯 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['roast'])
def roast_cmd(message):
    if not check_membership_required(message):
        return
    if not check_cooldown(message.from_user.id, 5):
        return

    name = message.reply_to_message.from_user.first_name if message.reply_to_message else message.from_user.first_name

    msg = bot.send_message(message.chat.id, "🎭 ...")
    response = ask_ai(f"رُست دوستانه {name}", system_prompt="کمدین", uid=message.from_user.id)
    bot.edit_message_text(f"🎭 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['compliment'])
def compliment_cmd(message):
    if not check_membership_required(message):
        return
    if not check_cooldown(message.from_user.id, 5):
        return

    name = message.reply_to_message.from_user.first_name if message.reply_to_message else message.from_user.first_name

    msg = bot.send_message(message.chat.id, "💝 ...")
    response = ask_ai(f"تعریف از {name}", system_prompt="مهربان", uid=message.from_user.id)
    bot.edit_message_text(f"💝 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

@bot.message_handler(commands=['motivation'])
def motivation_cmd(message):
    if not check_membership_required(message):
        return
    if not check_cooldown(message.from_user.id, 3):
        return

    msg = bot.send_message(message.chat.id, "💪 ...")
    response = ask_ai("جمله انگیزشی", system_prompt="انگیزشی", uid=message.from_user.id)
    bot.edit_message_text(f"💪 {response}", message.chat.id, msg.message_id, reply_markup=close_btn())

# ============================================================
# 💬 چت AI
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in ai_chat_users and m.chat.type == "private")
def ai_chat(message):
    text = message.text
    uid = message.from_user.id

    if text.startswith('/') or text in MENU_BUTTONS:
        close_ai_session(uid)
        return

    if time.time() - ai_last_active.get(uid, 0) > AI_TIMEOUT:
        close_ai_session(uid)
        bot.reply_to(message, "⏰ چت بسته شد", reply_markup=main_menu())
        return

    ai_last_active[uid] = time.time()

    history = chat_histories.get(uid, [])
    user_questions = len([h for h in history if h['role'] == 'user'])

    if not is_premium(uid) and user_questions >= MAX_AI_QUESTIONS:
        close_ai_session(uid)
        bot.reply_to(message, f"🔢 به محدودیت {MAX_AI_QUESTIONS} سوال رسیدی!", reply_markup=main_menu())
        return

    if not check_cooldown(uid, 2):
        return

    model = get_user_model(uid)
    msg = bot.send_message(message.chat.id, f"{model['name'].split()[0]} ...")
    response = ask_ai(text, history, uid=uid, model_override=model)

    history.append({"role": "user", "text": text})
    history.append({"role": "assistant", "text": response})
    chat_histories[uid] = history[-20:]

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("❌ خروج", callback_data="close_ai"))

    try:
        bot.edit_message_text(f"{model['name'].split()[0]} {response[:4000]}", message.chat.id, msg.message_id, reply_markup=markup)
    except:
        pass

    add_points(uid, 1)

@bot.callback_query_handler(func=lambda c: c.data == "close_ai")
def close_ai_cb(call):
    close_ai_session(call.from_user.id)
    bot.edit_message_text("✅ چت بسته شد", call.message.chat.id, call.message.message_id)
    bot.send_message(call.message.chat.id, "👺 منو:", reply_markup=main_menu())

# ============================================================
# هندلر حالت‌ها
# ============================================================
@bot.message_handler(func=lambda m: m.from_user.id in user_states and m.chat.type == "private")
def state_handler(message):
    uid = message.from_user.id
    state = user_states[uid].get('state')
    text = message.text

    if text.startswith('/') or text in MENU_BUTTONS:
        user_states.pop(uid, None)
        return

    if state == "waiting_broadcast":
        user_states.pop(uid, None)
        success, fail = 0, 0
        for u in users.keys():
            try:
                bot.send_message(u, f"📢 **پیام:**\n\n{text}", parse_mode="Markdown")
                success += 1
            except:
                fail += 1
        bot.reply_to(message, f"✅ {success} | ❌ {fail}", reply_markup=main_menu())

    elif state == "waiting_gift_code":
        user_states.pop(uid, None)
        message.text = f"/redeem {text}"
        redeem_code(message)

    elif state == "whisper_waiting_id":
        try:
            to_id = int(text)
            user_states[uid] = {'state': 'whisper_waiting_msg', 'to_id': to_id}
            bot.reply_to(message, "💌 پیامت:")
        except:
            bot.reply_to(message, "❌ آیدی عدد باشه!")
            user_states.pop(uid, None)

    elif state == "whisper_waiting_msg":
        to_id = user_states[uid].get('to_id')
        user_states.pop(uid, None)
        code = generate_whisper_code()
        whisper_data[code] = {'from_id': uid, 'to_id': to_id, 'message': text, 'seen': False}
        link = f"https://t.me/{bot.get_me().username}?start=whisper_{code}"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 لینک", url=link))
        bot.send_message(message.chat.id, "✅ نجوا آماده!", reply_markup=markup)
        add_points(uid, 2)

# ============================================================
# 👮 مدیریت رتبه
# ============================================================
@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if not is_owner(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/addadmin ID`", parse_mode="Markdown")
        return
    if uid not in ranks['admins']:
        ranks['admins'].append(uid)
    bot.reply_to(message, f"✅ `{uid}` ⚔️ ادمین شد! + ۶ مدل AI", parse_mode="Markdown")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if not is_owner(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if uid and uid in ranks['admins']:
        ranks['admins'].remove(uid)
        bot.reply_to(message, "✅ حذف شد")

@bot.message_handler(commands=['addlegend'])
def add_legend(message):
    if not is_admin_rank(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/addlegend ID`", parse_mode="Markdown")
        return
    if uid not in ranks['legend']:
        ranks['legend'].append(uid)
    for r in ['vip', 'premium', 'plus']:
        if uid in ranks[r]:
            ranks[r].remove(uid)
    bot.reply_to(message, f"✅ `{uid}` 🔮 افسانه! + ۵ مدل AI", parse_mode="Markdown")

@bot.message_handler(commands=['addvip'])
def add_vip(message):
    if not is_admin_rank(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/addvip ID`", parse_mode="Markdown")
        return
    if uid not in ranks['vip']:
        ranks['vip'].append(uid)
    for r in ['premium', 'plus']:
        if uid in ranks[r]:
            ranks[r].remove(uid)
    bot.reply_to(message, f"✅ `{uid}` 💎 ویژه! + ۴ مدل AI + تصویر", parse_mode="Markdown")

@bot.message_handler(commands=['addpremium'])
def add_premium(message):
    if not is_admin_rank(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/addpremium ID`", parse_mode="Markdown")
        return
    if uid not in ranks['premium']:
        ranks['premium'].append(uid)
    if uid in ranks['plus']:
        ranks['plus'].remove(uid)
    bot.reply_to(message, f"✅ `{uid}` 💜 پریمیوم! + ۳ مدل AI", parse_mode="Markdown")

@bot.message_handler(commands=['addplus'])
def add_plus(message):
    if not is_admin_rank(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/addplus ID`", parse_mode="Markdown")
        return
    if uid not in ranks['plus']:
        ranks['plus'].append(uid)
    bot.reply_to(message, f"✅ `{uid}` ⭐ پلاس! + ۲ مدل AI", parse_mode="Markdown")

@bot.message_handler(commands=['removeplus', 'removevip', 'removepremium', 'removelegend'])
def remove_rank(message):
    if not is_admin_rank(message.from_user.id):
        return
    uid, _ = get_uid_from_message(message)
    if not uid:
        return

    cmd = message.text.split()[0].replace('/remove', '')
    if cmd in ranks and uid in ranks[cmd]:
        ranks[cmd].remove(uid)
        bot.reply_to(message, "✅ حذف شد")

@bot.message_handler(commands=['ranks'])
def ranks_cmd(message):
    if not is_admin_rank(message.from_user.id):
        return
    text = f"""📊 **رتبه‌ها**

👑 مالک: {len(ranks['owners'])}
⚔️ ادمین: {len(ranks['admins'])}
🔮 افسانه: {len(ranks['legend'])}
💎 ویژه: {len(ranks['vip'])}
💜 پریمیوم: {len(ranks['premium'])}
⭐ پلاس: {len(ranks['plus'])}"""
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# ============================================================
# 👑 پنل مالک
# ============================================================
@bot.message_handler(commands=['panel', 'owner', 'admin'])
def owner_panel(message):
    if message.from_user.id not in ranks['owners']:
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 همگانی", callback_data="panel_sendall"),
        types.InlineKeyboardButton("🎁 ساخت کد", callback_data="panel_giftcode"),
        types.InlineKeyboardButton("📊 آمار", callback_data="panel_stats"),
        types.InlineKeyboardButton("👥 رتبه‌ها", callback_data="panel_ranks"),
        types.InlineKeyboardButton("🗑 پاک چت‌ها", callback_data="panel_clearall"),
        types.InlineKeyboardButton("💾 بکاپ", callback_data="panel_backup"),
        types.InlineKeyboardButton("🎁 کدها", callback_data="panel_codes"),
        types.InlineKeyboardButton("👥 دعوت‌ها", callback_data="panel_invites"),
        types.InlineKeyboardButton("❌ بستن", callback_data="close_msg")
    )

    bot.send_message(message.chat.id,
        f"👑 **پنل مالک**\n\n👥 کاربران: {len(users)}",
        parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("panel_"))
def panel_handler(call):
    if call.from_user.id not in ranks['owners']:
        bot.answer_callback_query(call.id, "❌")
        return

    action = call.data.replace("panel_", "")

    if action == "sendall":
        user_states[call.from_user.id] = {'state': 'waiting_broadcast'}
        bot.edit_message_text("📢 پیامت:\n\n/cancel برای لغو",
                             call.message.chat.id, call.message.message_id)

    elif action == "stats":
        text = f"""📊 **آمار**

👥 کاربران: {len(users)}
👑 مالک: {len(ranks['owners'])}
⚔️ ادمین: {len(ranks['admins'])}
🔮 افسانه: {len(ranks['legend'])}
💎 ویژه: {len(ranks['vip'])}
💜 پریمیوم: {len(ranks['premium'])}
⭐ پلاس: {len(ranks['plus'])}
🎁 کدها: {len(gift_codes)}
👥 دعوت‌ها: {sum(d['count'] for d in user_invites.values())}
🚫 بن: {len(banned_users)}"""
        bot.answer_callback_query(call.id)
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=close_btn())

    elif action == "ranks":
        text = "👥 **رتبه‌ها**\n\n"
        for rank_name, rank_list in [('⚔️ ادمین', ranks['admins']), ('🔮 افسانه', ranks['legend']),
                                     ('💎 ویژه', ranks['vip']), ('💜 پریمیوم', ranks['premium'])]:
            if rank_list:
                text += f"{rank_name}:\n" + '\n'.join([f"• `{uid}`" for uid in rank_list[:10]]) + "\n\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=close_btn())

    elif action == "invites":
        if not user_invites:
            bot.answer_callback_query(call.id, "📭 دعوتی نیست!")
            return

        sorted_invites = sorted(user_invites.items(), key=lambda x: x[1]['count'], reverse=True)[:10]
        text = "👥 **برترین دعوت‌کنندگان:**\n\n"
        for uid, data in sorted_invites:
            name = users.get(uid, {}).get('name', str(uid))[:15]
            text += f"• {name}: {data['count']} دعوت\n"

        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=close_btn())

    elif action == "clearall":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ بله", callback_data="confirm_clearall"),
            types.InlineKeyboardButton("❌ لغو", callback_data="close_msg")
        )
        bot.edit_message_text("⚠️ همه چت‌ها پاک بشه?",
                             call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif action == "backup":
        backup_data = {
            'users': users,
            'ranks': ranks,
            'gift_codes': gift_codes,
            'user_points': user_points,
            'user_level': user_level,
            'banned_users': list(banned_users),
            'user_invites': user_invites,
            'timed_ranks': {k: {'rank': v['rank'], 'expires': str(v['expires'])} for k, v in timed_ranks.items()}
        }
        backup_text = json.dumps(backup_data, ensure_ascii=False, indent=2)

        bot.send_document(call.message.chat.id,
                         io.BytesIO(backup_text.encode('utf-8')),
                         visible_file_name=f"backup_{datetime.now().strftime('%Y%m%d')}.json",
                         caption="💾 بکاپ")
        bot.answer_callback_query(call.id, "✅")

    elif action == "giftcode":
        bot.edit_message_text(
            "🎁 **ساخت کد**\n\n"
            "`/giftcode نوع مقدار تعداد [کد]`\n\n"
            "مثال:\n"
            "`/giftcode PLUS 1 10`\n"
            "`/giftcode VIP 1 5 GOJO`",
            call.message.chat.id, call.message.message_id,
            parse_mode="Markdown", reply_markup=close_btn())

    elif action == "codes":
        if not gift_codes:
            bot.answer_callback_query(call.id, "📭 کدی نیست!")
            return
        text = "🎁 **کدها:**\n\n"
        for code, data in list(gift_codes.items())[:15]:
            status = "✅" if data['uses'] < data['max_uses'] else "❌"
            text += f"{status} `{code}` | {data['type']} | {data['uses']}/{data['max_uses']}\n"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id,
                             parse_mode="Markdown", reply_markup=close_btn())

@bot.callback_query_handler(func=lambda c: c.data == "confirm_clearall")
def confirm_clearall(call):
    if call.from_user.id not in ranks['owners']:
        return

    chat_histories.clear()
    ai_chat_users.clear()
    ai_last_active.clear()
    user_states.clear()
    ai_last_message.clear()
    ai_context.clear()

    bot.answer_callback_query(call.id, "✅ پاک شد!")
    bot.edit_message_text("✅ چت‌ها پاک شد!", call.message.chat.id, call.message.message_id)

# ============================================================
# 🚫 بن کردن
# ============================================================
@bot.message_handler(commands=['banuser', 'globalban'])
def ban_user_cmd(message):
    if message.from_user.id not in ranks['owners']:
        return

    uid, _ = get_uid_from_message(message)
    if not uid:
        bot.reply_to(message, "`/banuser ID`", parse_mode="Markdown")
        return

    banned_users.add(uid)
    bot.reply_to(message, f"🚫 `{uid}` بن شد!", parse_mode="Markdown")

@bot.message_handler(commands=['unbanuser', 'globalunban'])
def unban_user_cmd(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split()
    if len(args) < 2:
        bot.reply_to(message, "`/unbanuser ID`", parse_mode="Markdown")
        return

    try:
        uid = int(args[1])
        banned_users.discard(uid)
        bot.reply_to(message, f"✅ `{uid}` آنبن!", parse_mode="Markdown")
    except:
        pass

# ============================================================
# 📢 ارسال همگانی
# ============================================================
@bot.message_handler(commands=['sendall', 'broadcast'])
def sendall_cmd(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        user_states[message.from_user.id] = {'state': 'waiting_broadcast'}
        bot.reply_to(message, "📢 پیامت:\n\n/cancel")
        return

    text = args[1]
    success, fail = 0, 0

    msg = bot.reply_to(message, "📤 ارسال...")

    for uid in users.keys():
        try:
            bot.send_message(uid, f"📢 **پیام:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except:
            fail += 1

    bot.edit_message_text(f"✅ {success} | ❌ {fail}", message.chat.id, msg.message_id)

# ============================================================
# 🪙 دادن امتیاز
# ============================================================
@bot.message_handler(commands=['givepoints'])
def give_points_cmd(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "`/givepoints ID مقدار`", parse_mode="Markdown")
        return

    try:
        uid = int(args[1])
        amount = int(args[2])
        if uid not in user_points:
            user_points[uid] = 0
            user_level[uid] = 1
        user_points[uid] += amount
        bot.reply_to(message, f"✅ {amount}⭐ به `{uid}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ خطا!")

@bot.message_handler(commands=['givelevel'])
def give_level_cmd(message):
    if message.from_user.id not in ranks['owners']:
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "`/givelevel ID مقدار`", parse_mode="Markdown")
        return

    try:
        uid = int(args[1])
        amount = int(args[2])
        if uid not in user_level:
            user_level[uid] = 1
        user_level[uid] += amount
        bot.reply_to(message, f"✅ {amount} لول به `{uid}`", parse_mode="Markdown")
    except:
        bot.reply_to(message, "❌ خطا!")

# ============================================================
# 👮 مدیریت گروه
# ============================================================
@bot.message_handler(commands=['warn'])
def warn_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام کسی ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    target = message.reply_to_message.from_user

    if is_group_admin(message.chat.id, target.id):
        bot.reply_to(message, "❌ نمیتونی به ادمین warn بدی!")
        return

    key = f"{message.chat.id}_{target.id}"
    warnings[key] = warnings.get(key, 0) + 1

    bot.send_message(message.chat.id,
        f"⚠️ **{target.first_name}** اخطار گرفت!\n"
        f"📊 اخطار: {warnings[key]}/3",
        parse_mode="Markdown")

    if warnings[key] >= 3:
        try:
            bot.ban_chat_member(message.chat.id, target.id)
            bot.send_message(message.chat.id, f"🚫 **{target.first_name}** بن شد! (۳ اخطار)", parse_mode="Markdown")
            warnings[key] = 0
        except Exception as e:
            bot.reply_to(message, f"❌ خطا در بن: بات ادمین نیست یا دسترسی نداره")

@bot.message_handler(commands=['mute'])
def mute_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    if not bot_is_admin(message.chat.id):
        bot.reply_to(message, "❌ بات ادمین نیست! اول بات رو ادمین کن.")
        return

    target = message.reply_to_message.from_user

    if is_group_admin(message.chat.id, target.id):
        bot.reply_to(message, "❌ نمیتونی ادمین رو میوت کنی!")
        return

    try:
        bot.restrict_chat_member(
            message.chat.id,
            target.id,
            until_date=datetime.now() + timedelta(hours=1),
            permissions=types.ChatPermissions(can_send_messages=False)
        )
        bot.send_message(message.chat.id, f"🔇 **{target.first_name}** میوت شد (۱ ساعت)", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)[:50]}")

@bot.message_handler(commands=['unmute'])
def unmute_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    if not bot_is_admin(message.chat.id):
        bot.reply_to(message, "❌ بات ادمین نیست!")
        return

    target = message.reply_to_message.from_user

    try:
        bot.restrict_chat_member(
            message.chat.id,
            target.id,
            permissions=types.ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
        )
        bot.send_message(message.chat.id, f"🔊 **{target.first_name}** آنمیوت شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)[:50]}")

@bot.message_handler(commands=['kick'])
def kick_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    if not bot_is_admin(message.chat.id):
        bot.reply_to(message, "❌ بات ادمین نیست!")
        return

    target = message.reply_to_message.from_user

    if is_group_admin(message.chat.id, target.id):
        bot.reply_to(message, "❌ نمیتونی ادمین رو کیک کنی!")
        return

    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.unban_chat_member(message.chat.id, target.id)
        bot.send_message(message.chat.id, f"👢 **{target.first_name}** کیک شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)[:50]}")

@bot.message_handler(commands=['ban'])
def ban_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    if not bot_is_admin(message.chat.id):
        bot.reply_to(message, "❌ بات ادمین نیست!")
        return

    target = message.reply_to_message.from_user

    if is_group_admin(message.chat.id, target.id):
        bot.reply_to(message, "❌ نمیتونی ادمین رو بن کنی!")
        return

    try:
        bot.ban_chat_member(message.chat.id, target.id)
        bot.send_message(message.chat.id, f"🚫 **{target.first_name}** بن شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)[:50]}")

@bot.message_handler(commands=['unban'])
def unban_cmd(message):
    if message.chat.type == "private":
        bot.reply_to(message, "❌ فقط در گروه!")
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        bot.reply_to(message, "❌ فقط ادمین‌ها!")
        return

    if not bot_is_admin(message.chat.id):
        bot.reply_to(message, "❌ بات ادمین نیست!")
        return

    target = message.reply_to_message.from_user

    try:
        bot.unban_chat_member(message.chat.id, target.id)
        bot.send_message(message.chat.id, f"✅ **{target.first_name}** آنبن شد!", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ خطا: {str(e)[:50]}")

@bot.message_handler(commands=['del'])
def delete_cmd(message):
    if message.chat.type == "private":
        return

    if not message.reply_to_message:
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        return

    try:
        bot.delete_message(message.chat.id, message.reply_to_message.message_id)
        bot.delete_message(message.chat.id, message.message_id)
    except:
        pass

@bot.message_handler(commands=['clearwarn', 'resetwarn'])
def clear_warn_cmd(message):
    if message.chat.type == "private":
        return

    if not message.reply_to_message:
        bot.reply_to(message, "💡 روی پیام ریپلای کن!")
        return

    sender_id = message.from_user.id
    if not is_group_admin(message.chat.id, sender_id) and not is_admin_rank(sender_id):
        return

    target = message.reply_to_message.from_user
    key = f"{message.chat.id}_{target.id}"

    if key in warnings:
        warnings[key] = 0
        bot.send_message(message.chat.id, f"✅ اخطارهای **{target.first_name}** پاک شد!", parse_mode="Markdown")
    else:
        bot.reply_to(message, "این کاربر اخطاری نداره!")

# ============================================================
# 🛠 ابزارها
# ============================================================
@bot.message_handler(commands=['id'])
def id_cmd(message):
    if message.reply_to_message:
        u = message.reply_to_message.from_user
        bot.reply_to(message,
            f"👤 {u.first_name}\n🆔 `{u.id}`\n🏅 {get_rank_name(u.id)}",
            parse_mode="Markdown")
    else:
        bot.reply_to(message, f"🆔 `{message.from_user.id}`", parse_mode="Markdown")

@bot.message_handler(commands=['ping'])
def ping_cmd(message):
    s = time.time()
    m = bot.send_message(message.chat.id, "🏓")
    bot.edit_message_text(f"🏓 {int((time.time()-s)*1000)}ms", message.chat.id, m.message_id)

@bot.message_handler(commands=['stats'])
def stats_cmd(message):
    if not is_owner(message.from_user.id):
        return
    bot.send_message(message.chat.id,
        f"📊 کاربران: {len(users)}\n⚔️ ادمین: {len(ranks['admins'])}\n💎 ویژه: {len(ranks['vip'])}\n⭐ پلاس: {len(ranks['plus'])}")

# ============================================================
# 👋 خوشامد گروه
# ============================================================
@bot.message_handler(content_types=['new_chat_members'])
def welcome(message):
    for u in message.new_chat_members:
        if u.id == bot.get_me().id:
            bot.send_message(message.chat.id,
                "👺 سلام! **گوجو v7.3** فعال شد!\n\n"
                "📋 /menu - منو\n"
                "💌 /whisper - نجوا\n"
                "🤫 /confess - اعتراف\n\n"
                "⚠️ **مهم:** برای استفاده از دستورات مدیریت (warn/mute/kick/ban) بات رو ادمین کنید!",
                parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id,
                f"👋 سلام **{u.first_name}**!\n📋 /menu",
                parse_mode="Markdown")

# ============================================================
# 📋 منو در گروه
# ============================================================
@bot.message_handler(commands=['menu'])
def menu_cmd(message):
    if message.chat.type == "private":
        bot.send_message(message.chat.id, "👺 منو:", reply_markup=main_menu())
    else:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("💌 نجوا", callback_data="group_whisper"),
            types.InlineKeyboardButton("🤫 اعتراف", callback_data="group_confess"),
            types.InlineKeyboardButton("🎲 تاس", callback_data="group_dice"),
            types.InlineKeyboardButton("😂 جوک", callback_data="group_joke"),
            types.InlineKeyboardButton("🤖 ربات", url=f"https://t.me/{bot.get_me().username}")
        )
        bot.send_message(message.chat.id, "👺 **گوجو**", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: c.data.startswith("group_"))
def group_menu_handler(call):
    action = call.data.replace("group_", "")

    if action == "whisper":
        bot.answer_callback_query(call.id, "💌 /whisper @user پیام", show_alert=True)
    elif action == "confess":
        bot.answer_callback_query(call.id, "🤫 /confess متن", show_alert=True)
    elif action == "dice":
        bot.send_dice(call.message.chat.id)
        bot.answer_callback_query(call.id)
    elif action == "joke":
        jokes = ["😂 چرا ماهی تلفن نداره؟", "😂 چرا کلاغ سیاهه؟"]
        bot.send_message(call.message.chat.id, random.choice(jokes))
        bot.answer_callback_query(call.id)

# ============================================================
# 🚀 اجرا
# ============================================================
if __name__ == "__main__":
    print("=" * 50)
    print("👺 گوجو v7.3 - Fixed & Improved")
    print("=" * 50)
    print("✅ مدل‌های AI اصلاح شد (با Fallback)")
    print("✅ ریپلای روی پاسخ AI کار میکنه")
    print("✅ انتخاب مدل با /ai")
    print("✅ همه تغییرات قبلی حفظ شد")
    print("=" * 50)

    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
