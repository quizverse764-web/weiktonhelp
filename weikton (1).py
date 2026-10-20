"""
WEIKTON HELP BOT — всё управляется кнопками
"""

import asyncio
import logging
import random
import aiosqlite
import json
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ChatPermissions, ErrorEvent
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ChatMemberStatus

# ==================== НАСТРОЙКИ ====================
TOKEN = "1780243674:hhORgOx8R4jXmDq6Wdg_h_IlIUiWR14m5ZL"
# Админы бота по username (без @, регистр не важен)
GLOBAL_ADMIN_USERNAMES = ["weikton"]
BOT_NAME = "WEIKTON HELP BOT"
VERSION = "7.0.0 BUTTONS"
DB_NAME = "freeze_zomelezz.db"

START_BALANCE = 500
DAILY_BONUS_BASE = 100
DAILY_STREAK_BONUS = 20
MAX_STREAK = 7
TRANSFER_TAX = 0.05
LOAN_INTEREST = 0.15
BANK_INTEREST = 0.02
ROB_COOLDOWN_HOURS = 4
ROB_SUCCESS_CHANCE = 0.35
ROB_MAX_AMOUNT = 5000
CLAN_CREATE_COST = 1000
MIN_BET = 10

RANKS = {
    5: {"name": "👑 Создатель", "perms": ["all"]},
    4: {"name": "🛡️ Главный админ", "perms": ["ban", "kick", "mute", "warn", "setrank", "give", "settings", "logs", "reply_support", "broadcast", "gban"]},
    3: {"name": "🎧 Агент поддержки", "perms": ["reply_support", "warn"]},
    2: {"name": "⚔️ Модератор", "perms": ["ban", "kick", "mute", "warn"]},
    1: {"name": "👤 Пользователь", "perms": []},
    0: {"name": "🚫 Забанен", "perms": []}
}

# ==================== МАГАЗИН ====================
SHOP = {
    "vip":         {"emoji": "💎", "name": "VIP на 7 дней", "price": 5000,
                    "desc": "+50% к дейли, +25% к работе и значок 💎 в профиле. Повторная покупка продлевает срок."},
    "vip30":       {"emoji": "👑", "name": "VIP на 30 дней", "price": 15000,
                    "desc": "Все бонусы VIP на целый месяц — выгоднее, чем брать по неделе."},
    "nick":        {"emoji": "📝", "name": "Смена ника", "price": 500,
                    "desc": "Новое имя в профиле, топах и переводах."},
    "bio":         {"emoji": "📋", "name": "Биография", "price": 200,
                    "desc": "Короткий текст о себе в профиле (до 100 символов)."},
    "title":       {"emoji": "🏷", "name": "Свой титул", "price": 1500,
                    "desc": "Надпись рядом с ником, например «Король слотов» (до 20 символов)."},
    "badge":       {"emoji": "🎖", "name": "Значок профиля", "price": 300,
                    "desc": "Эмодзи перед ником. Выбираете из набора после покупки."},
    "shield":      {"emoji": "🛡", "name": "Щит от ограбления (24ч)", "price": 1000,
                    "desc": "Сутки никто не сможет вас ограбить."},
    "lockpick":    {"emoji": "🗝", "name": "Отмычка", "price": 700,
                    "desc": "+25% к шансу успешного ограбления. Тратится сама при попытке."},
    "luck":        {"emoji": "🍀", "name": "Амулет удачи (6ч)", "price": 1200,
                    "desc": "+10% к шансу ограбления, +15% к выигрышам из кейсов и +10% к зарплате."},
    "work_reset":  {"emoji": "⏱", "name": "Сброс «Работы»", "price": 300,
                    "desc": "Можно работать снова прямо сейчас, без ожидания."},
    "daily_reset": {"emoji": "🔄", "name": "Сброс «Дейли»", "price": 600,
                    "desc": "Забрать ежедневный бонус снова, не дожидаясь суток. Стрик сохраняется."},
    "pet_dog":     {"emoji": "🐶", "name": "Собака", "price": 500, "pet": "🐶 Собака",
                    "desc": "Верный друг. Хороший доход и бодрый характер."},
    "pet_cat":     {"emoji": "🐱", "name": "Кошка", "price": 500, "pet": "🐱 Кошка",
                    "desc": "Независимая, но приносит монетки."},
    "pet_hamster": {"emoji": "🐹", "name": "Хомяк", "price": 400, "pet": "🐹 Хомяк",
                    "desc": "Самый дешёвый питомец, запасливый."},
    "pet_rabbit":  {"emoji": "🐰", "name": "Кролик", "price": 400, "pet": "🐰 Кролик",
                    "desc": "Быстрый и весёлый."},
    "pet_fox":     {"emoji": "🦊", "name": "Лиса", "price": 800, "pet": "🦊 Лиса",
                    "desc": "Хитрая — доход чуть выше обычного."},
    "pet_dragon":  {"emoji": "🐉", "name": "Дракончик", "price": 3000, "pet": "🐉 Дракончик",
                    "desc": "Редкий питомец: приносит вдвое больше дохода."},
    "pet_food":    {"emoji": "🍖", "name": "Премиум-корм ×3", "price": 200,
                    "desc": "Три порции: каждая восстанавливает 60 сытости бесплатно (обычный корм — 30 за 20 ❄️)."},
}
SHOP_CATS = {
    "status": ("💎 Статусы", ["vip", "vip30"]),
    "look":   ("✨ Внешний вид", ["nick", "bio", "title", "badge"]),
    "boost":  ("⚡ Бусты", ["shield", "lockpick", "luck", "work_reset", "daily_reset"]),
    "pet":    ("🐾 Для питомцев", ["pet_dog", "pet_cat", "pet_hamster", "pet_rabbit", "pet_fox", "pet_dragon", "pet_food"]),
}
BADGES = ["🔥", "⭐", "👑", "🐉", "🍀", "💀", "❄️", "🚀", "🌈"]

# ==================== ИГРЫ ====================
SLOT_SYMBOLS = ["🍒", "🍋", "🍊", "🍇", "💎", "7️⃣", "⭐"]
SLOT_PAYOUTS = {"🍒": 4, "🍋": 6, "🍊": 8, "🍇": 10, "💎": 20, "7️⃣": 35, "⭐": 50}  # итоговая выплата ×ставка при тройке

ROULETTE_RED = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]

# (цена, [(выигрыш, вес), ...]) — средний возврат около 95%
CASES = {
    "📦 Обычный — 100❄️":        (100,   [(0, 25), (50, 35), (100, 25), (200, 10), (500, 5)]),
    "🎁 Редкий — 500❄️":         (500,   [(0, 25), (250, 30), (500, 25), (1000, 15), (2500, 5)]),
    "💎 Эпический — 2000❄️":     (2000,  [(0, 25), (1000, 30), (2000, 25), (4000, 15), (10000, 5)]),
    "👑 Легендарный — 10000❄️":  (10000, [(0, 30), (5000, 30), (10000, 22), (20000, 13), (50000, 5)]),
}

WHEEL_PRIZES = [(25, 20), (50, 30), (100, 25), (250, 15), (500, 7), (1000, 3)]

RP_ACTIONS = {
    "🤗 Обнять":     ("🤗", "обнял(а)", ["крепко", "нежно", "тепло"]),
    "💋 Поцеловать": ("💋", "поцеловал(а)", ["в щёчку", "в лоб", "нежно"]),
    "👊 Ударить":    ("👊", "ударил(а)", ["по плечу", "шутя", "слегка"]),
    "🖐 Погладить":  ("🖐", "погладил(а)", ["по голове", "нежно", "ласково"]),
    "🦷 Укусить":    ("🦷", "укусил(а)", ["за палец", "слегка", "за ухо"]),
    "🔫 Выстрелить": ("🔫", "выстрелил(а) в", ["водяным пистолетом", "из рогатки", "хлопушкой"]),
}

JOKES = ["Почему программисты путают Хэллоуин и Рождество? 31 OCT = 25 DEC.", "Колобок повесился.", "Идёт медведь, видит машина горит. Сел и сгорел."]
FACTS = ["Кошки спят 70% жизни.", "Банан — это ягода.", "Сердце креветки в голове."]
QUOTES = ["Будь собой — Оскар Уайльд", "Жизнь — то, что происходит, пока ты строишь планы — Леннон"]
BALL_ANSWERS = ["Бесспорно", "Предрешено", "Да", "Нет", "Спроси позже", "Весьма сомнительно"]

# ==================== ЗАПУСК БОТА ====================
logging.basicConfig(level=logging.INFO)
# Bot API сервера UraganGram (не официальный Telegram)
API_BASE = "http://31.77.251.113:9930"
session = AiohttpSession(api=TelegramAPIServer.from_base(API_BASE))
bot = Bot(token=TOKEN, session=session)
dp = Dispatcher()

_ADMIN_USERNAMES = {u.lstrip("@").lower() for u in GLOBAL_ADMIN_USERNAMES}
ADMIN_ID_CACHE = set()  # ID админов, определённые по username при их активности
db = None
pending = {}            # user_id -> состояние диалога (ждём ввод/выбор)
duel_requests = {}      # target_id -> {"from", "bet", "ts"}
marry_requests = {}     # target_id -> {"from", "ts"}


def is_global_admin(user) -> bool:
    username = (getattr(user, "username", None) or "").lower()
    if username in _ADMIN_USERNAMES:
        ADMIN_ID_CACHE.add(user.id)
        return True
    ADMIN_ID_CACHE.discard(user.id)
    return False


@dp.update.outer_middleware()
async def user_middleware(handler, event, data):
    user = data.get("event_from_user")
    if user and not user.is_bot and db is not None:
        admin = is_global_admin(user)
        try:
            await touch_user(user)
            if not admin and await check_gban(user.id):
                return  # глобально забаненные не получают ответов
        except Exception:
            logging.exception("user_middleware")
    return await handler(event, data)


@dp.error()
async def on_error(event: ErrorEvent):
    logging.exception("Ошибка обработчика: %s", event.exception)
    m = getattr(event.update, "message", None)
    if m:
        try:
            await m.answer("⚠️ Что-то пошло не так. Попробуйте ещё раз.")
        except Exception:
            pass
    return True


# ==================== БАЗА ДАННЫХ ====================
async def init_db():
    global db
    db = await aiosqlite.connect(DB_NAME)
    db.row_factory = aiosqlite.Row

    await db.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY, name TEXT, nickname TEXT, balance INTEGER DEFAULT 500,
        rep INTEGER DEFAULT 0, warns INTEGER DEFAULT 0, marry_id INTEGER, marry_id2 INTEGER,
        status TEXT DEFAULT '👤 Пользователь', bio TEXT, global_rank INTEGER DEFAULT 1,
        prefix TEXT DEFAULT '/', daily_streak INTEGER DEFAULT 0, last_daily TEXT,
        loan_amount INTEGER DEFAULT 0, loan_date TEXT, rob_cooldown TEXT, work_cooldown TEXT,
        xp INTEGER DEFAULT 0, level INTEGER DEFAULT 1, clan_id INTEGER)""")
    # новые колонки (для старых баз)
    for col in ("username TEXT", "title TEXT", "badge TEXT"):
        try:
            await db.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except Exception:
            pass

    await db.execute("""CREATE TABLE IF NOT EXISTS user_ranks (
        user_id INTEGER, chat_id INTEGER, rank INTEGER DEFAULT 1, PRIMARY KEY (user_id, chat_id))""")
    await db.execute("""CREATE TABLE IF NOT EXISTS chats (
        chat_id INTEGER PRIMARY KEY, welcome INTEGER DEFAULT 1, warn_limit INTEGER DEFAULT 3,
        welcome_text TEXT, rules TEXT, antiflood INTEGER DEFAULT 0, antimat INTEGER DEFAULT 0,
        antilink INTEGER DEFAULT 0)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS warns (
        id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, user_id INTEGER,
        reason TEXT, date TEXT, warned_by INTEGER)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, admin_id INTEGER, action TEXT,
        target TEXT, chat_id INTEGER, reason TEXT, date TEXT)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS bank (
        user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS clans (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, tag TEXT UNIQUE,
        owner_id INTEGER, balance INTEGER DEFAULT 0, level INTEGER DEFAULT 1,
        members TEXT DEFAULT '[]', created TEXT)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS pets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, owner_id INTEGER UNIQUE, type TEXT,
        name TEXT, level INTEGER DEFAULT 1, xp INTEGER DEFAULT 0, hunger INTEGER DEFAULT 100,
        happiness INTEGER DEFAULT 100, energy INTEGER DEFAULT 100, created TEXT)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY, reward INTEGER, uses INTEGER DEFAULT 1,
        used_by TEXT DEFAULT '[]', created_by INTEGER)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, username TEXT,
        question TEXT, status TEXT DEFAULT 'open', created TEXT)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS gbans (
        user_id INTEGER PRIMARY KEY, reason TEXT, date TEXT, banned_by INTEGER)""")
    await db.execute("""CREATE TABLE IF NOT EXISTS mutes (
        user_id INTEGER, chat_id INTEGER, until TEXT, PRIMARY KEY (user_id, chat_id))""")
    await db.execute("""CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER, item TEXT, qty INTEGER DEFAULT 0, PRIMARY KEY (user_id, item))""")
    await db.execute("""CREATE TABLE IF NOT EXISTS effects (
        user_id INTEGER, key TEXT, until TEXT, PRIMARY KEY (user_id, key))""")
    await db.commit()
    print("✅ База данных готова")


# ==================== ПОМОЩНИКИ ====================
def dn(u) -> str:
    """Отображаемое имя игрока."""
    return u["nickname"] or u["name"] or str(u["user_id"])


def fmt(n) -> str:
    return f"{int(n):,}".replace(",", " ")


def bar(v, mx=100, n=10) -> str:
    filled = max(0, min(n, int(round(n * v / mx))))
    return "█" * filled + "░" * (n - filled)


def left_str(seconds) -> str:
    seconds = int(max(0, seconds))
    h, r = divmod(seconds, 3600)
    m = r // 60
    return f"{h}ч {m}м" if h else f"{max(m, 1)}м"


def to_int(text):
    try:
        return int(str(text).strip().replace(" ", "").replace("_", ""))
    except Exception:
        return None


def parse_dt(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except Exception:
        return None


async def touch_user(u):
    """Создаёт игрока и запоминает его имя и username."""
    async with db.execute("SELECT name, username FROM users WHERE user_id = ?", (u.id,)) as c:
        row = await c.fetchone()
    if not row:
        await db.execute("INSERT INTO users (user_id, name, nickname, username, balance) VALUES (?, ?, ?, ?, ?)",
                         (u.id, u.full_name, u.full_name, u.username, START_BALANCE))
        await db.commit()
    elif row["name"] != u.full_name or (row["username"] or "") != (u.username or ""):
        await db.execute("UPDATE users SET name = ?, username = ? WHERE user_id = ?", (u.full_name, u.username, u.id))
        await db.commit()


async def get_user(user_id: int, name: str = "Пользователь"):
    async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
        user = await cursor.fetchone()
    if not user:
        await db.execute("INSERT INTO users (user_id, name, nickname, balance) VALUES (?, ?, ?, ?)",
                         (user_id, name, name, START_BALANCE))
        await db.commit()
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
    return user


async def find_user(query: str):
    """Поиск игрока по @username, ID или нику."""
    q = (query or "").strip().lstrip("@")
    if not q:
        return None
    if q.isdigit():
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (int(q),)) as c:
            r = await c.fetchone()
        if r:
            return r
    async with db.execute("SELECT * FROM users WHERE lower(username) = lower(?)", (q,)) as c:
        r = await c.fetchone()
    if r:
        return r
    async with db.execute("SELECT * FROM users WHERE lower(name) LIKE lower(?) OR lower(nickname) LIKE lower(?) LIMIT 1",
                          (f"%{q}%", f"%{q}%")) as c:
        return await c.fetchone()


async def spend(uid: int, amount: int) -> bool:
    """Списывает ❄️, только если их хватает."""
    if amount < 0:
        return False
    cur = await db.execute("UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?", (amount, uid, amount))
    ok = cur.rowcount == 1
    await db.commit()
    return ok


async def give(uid: int, amount: int):
    await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, uid))
    await db.commit()


async def add_xp(uid: int, n: int):
    u = await get_user(uid)
    xp = (u["xp"] or 0) + n
    await db.execute("UPDATE users SET xp = ?, level = ? WHERE user_id = ?", (xp, 1 + xp // 200, uid))
    await db.commit()


async def effect_until(uid: int, key: str):
    async with db.execute("SELECT until FROM effects WHERE user_id = ? AND key = ?", (uid, key)) as c:
        r = await c.fetchone()
    dt = parse_dt(r["until"]) if r else None
    return dt if dt and dt > datetime.now() else None


async def effect_active(uid: int, key: str) -> bool:
    return (await effect_until(uid, key)) is not None


async def effect_add(uid: int, key: str, hours: float):
    base = (await effect_until(uid, key)) or datetime.now()
    until = base + timedelta(hours=hours)
    await db.execute("INSERT INTO effects (user_id, key, until) VALUES (?, ?, ?) "
                     "ON CONFLICT(user_id, key) DO UPDATE SET until = excluded.until", (uid, key, until.isoformat()))
    await db.commit()
    return until


async def inv_get(uid: int, item: str) -> int:
    async with db.execute("SELECT qty FROM inventory WHERE user_id = ? AND item = ?", (uid, item)) as c:
        r = await c.fetchone()
    return r["qty"] if r else 0


async def inv_add(uid: int, item: str, n: int = 1):
    await db.execute("INSERT INTO inventory (user_id, item, qty) VALUES (?, ?, ?) "
                     "ON CONFLICT(user_id, item) DO UPDATE SET qty = qty + ?", (uid, item, n, n))
    await db.commit()


async def inv_take(uid: int, item: str) -> bool:
    if await inv_get(uid, item) <= 0:
        return False
    await db.execute("UPDATE inventory SET qty = qty - 1 WHERE user_id = ? AND item = ?", (uid, item))
    await db.commit()
    return True


async def get_pet(uid: int):
    async with db.execute("SELECT * FROM pets WHERE owner_id = ?", (uid,)) as c:
        return await c.fetchone()


async def get_user_rank(user_id: int, chat_id: int = None) -> int:
    if user_id in ADMIN_ID_CACHE:
        return 5
    if chat_id:
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status == ChatMemberStatus.CREATOR:
                return 5
            elif member.status == ChatMemberStatus.ADMINISTRATOR:
                return 4
        except Exception:
            pass
        async with db.execute("SELECT rank FROM user_ranks WHERE user_id = ? AND chat_id = ?", (user_id, chat_id)) as cursor:
            result = await cursor.fetchone()
            if result:
                return result[0]
    async with db.execute("SELECT global_rank FROM users WHERE user_id = ?", (user_id,)) as cursor:
        result = await cursor.fetchone()
        if result and result[0]:
            return result[0]
    return 1


async def has_perm(user_id: int, chat_id: int, permission: str) -> bool:
    rank = await get_user_rank(user_id, chat_id)
    if rank == 5:
        return True
    return permission in RANKS.get(rank, {}).get("perms", [])


async def check_gban(user_id: int) -> bool:
    async with db.execute("SELECT user_id FROM gbans WHERE user_id = ?", (user_id,)) as cursor:
        return await cursor.fetchone() is not None


async def log_action(admin_id: int, action: str, target: str, chat_id: int = 0, reason: str = ""):
    await db.execute("INSERT INTO logs (admin_id, action, target, chat_id, reason, date) VALUES (?, ?, ?, ?, ?, ?)",
                     (admin_id, action, target, chat_id, reason, datetime.now().isoformat()))
    await db.commit()


async def notify(user_id: int, text: str, kb=None) -> bool:
    """Личное сообщение игроку. False, если бот не может ему писать."""
    try:
        await bot.send_message(user_id, text, reply_markup=kb)
        return True
    except Exception:
        return False


# ==================== КЛАВИАТУРЫ ====================
BACK = "🔙 Назад"
CANCEL = "❌ Отмена"
BACK_ECO = "🔙 В экономику"
BACK_SHOP = "🔙 В магазин"
BACK_ADMIN = "🔙 В админку"
DUEL_YES, DUEL_NO = "⚔️ Принять дуэль", "❌ Отклонить дуэль"
MARRY_YES, MARRY_NO = "💍 Согласиться", "💔 Отказать"


def K(*rows):
    b = ReplyKeyboardBuilder()
    for row in rows:
        b.row(*[types.KeyboardButton(text=t) for t in row])
    return b.as_markup(resize_keyboard=True)


def labels(kb) -> set:
    return {b.text for row in kb.keyboard for b in row}


def main_menu():
    return K(["👤 Профиль", "💰 Баланс"], ["🎭 РП Действия", "💑 Брак"], ["📊 Топ", "🏆 Ранги"],
             ["🛒 Магазин", "🎮 Игры"], ["💼 Экономика", "🏰 Кланы"], ["🐾 Питомцы", "🎫 Поддержка"],
             ["⚙️ Админ-панель", "❓ Помощь"])


def profile_menu():
    return K(["✏️ Сменить ник", "📝 Сменить био"], ["🏷 Сменить титул", "🎖 Сменить значок"],
             ["🎒 Инвентарь", "🛒 Магазин"], [BACK])


def top_menu():
    return K(["💰 Богачи", "🏅 Уровни"], [BACK])


def rp_menu():
    return K(["🤗 Обнять", "💋 Поцеловать", "👊 Ударить"], ["🖐 Погладить", "🦷 Укусить", "🔫 Выстрелить"], [BACK])


def marry_menu():
    return K(["💍 Предложить брак", "💔 Развод"], ["👫 Мои браки"], [BACK])


def games_menu():
    return K(["🎰 Слоты", "🎲 Рулетка"], ["⚔️ Дуэль", "📦 Кейсы"], ["🪙 Монетка", "🎯 КНБ"], ["🎡 Колесо удачи", "🎱 Шар судьбы"], ["😄 Шутка", "📚 Факт", "💬 Цитата"], [BACK])


def economy_menu():
    return K(["💸 Перевод", "🏦 Банк"], ["🎁 Дейли", "💳 Кредит"], ["🦹 Грабеж", "💼 Работа"], ["🎟 Промокод"], [BACK])


def bank_menu():
    return K(["💰 Внести", "💵 Снять"], ["📈 Получить проценты"], [BACK_ECO])


def loan_menu():
    return K(["💳 Взять кредит", "✅ Погасить кредит"], [BACK_ECO])


def clan_menu():
    return K(["🏰 Мой клан", "🏰 Создать клан"], ["🚪 Вступить", "💰 Казна"], ["👥 Участники", "📊 Топ кланов"],
             ["⬆️ Улучшить клан", "🚶 Покинуть клан"], [BACK])


def pet_menu():
    return K(["🐾 Мой питомец", "🛒 Купить питомца"], ["🍖 Покормить", "🎮 Играть"], ["😴 Уложить спать", "💰 Доход питомца"],
             ["📛 Назвать", BACK])


def support_menu():
    return K(["✍️ Создать тикет", "📋 Мои тикеты"], [BACK])


def shop_menu():
    return K([SHOP_CATS["status"][0], SHOP_CATS["look"][0]], [SHOP_CATS["boost"][0], SHOP_CATS["pet"][0]],
             ["🎒 Инвентарь"], [BACK])


def admin_menu():
    return K(["📊 Статистика", "📋 Логи"], ["🎫 Тикеты", "💰 Выдать"], ["📢 Рассылка", "🎁 Промо-коды"],
             ["🔨 Глобальный бан", "🕊 Разбан"], ["🏆 Назначить ранг", "👥 Админы чата"], [BACK])


def promo_menu():
    return K(["➕ Создать промокод", "📋 Список промокодов"], ["🗑 Удалить промокод"], [BACK_ADMIN])


def tickets_menu():
    return K(["💬 Ответить на тикет", "✅ Закрыть тикет"], [BACK_ADMIN])


def bet_kb(back=BACK):
    return K(["💰 100", "💰 500", "💰 1000"], ["💰 5000", "💰 Всё"], [back])


def loan_kb():
    return K(["💰 500", "💰 1000", "💰 5000"], ["💰 10000"], [BACK_ECO])


def item_label(key: str) -> str:
    it = SHOP[key]
    return f"{it['emoji']} {it['name']} — {fmt(it['price'])}❄️"


ITEM_BY_LABEL = {item_label(k): k for k in SHOP}
CAT_BY_LABEL = {v[0]: k for k, v in SHOP_CATS.items()}


def cat_menu(cat: str):
    return K(*[[item_label(k)] for k in SHOP_CATS[cat][1]], [BACK_SHOP])


# Все «навигационные» кнопки: нажатие любой из них сбрасывает текущий диалог
NAV_TEXTS = set()
for _kb in (main_menu(), profile_menu(), top_menu(), rp_menu(), marry_menu(), games_menu(), economy_menu(), bank_menu(),
            loan_menu(), clan_menu(), pet_menu(), support_menu(), shop_menu(), admin_menu(), promo_menu(), tickets_menu(),
            *[cat_menu(c) for c in SHOP_CATS]):
    NAV_TEXTS |= labels(_kb)
NAV_TEXTS |= set(ITEM_BY_LABEL) | {CANCEL, BACK, BACK_ECO, BACK_SHOP, BACK_ADMIN, DUEL_YES, DUEL_NO, MARRY_YES, MARRY_NO}


# ==================== ДИАЛОГИ (ожидание ответа от игрока) ====================
ACTIONS = {}


def action(name):
    def deco(fn):
        ACTIONS[name] = fn
        return fn
    return deco


def set_state(uid: int, act: str, **data):
    pending[uid] = {"action": act, "ts": time.time(), **data}


def clear_state(uid: int):
    pending.pop(uid, None)


async def say(msg: Message, text: str, kb=None):
    await msg.answer(text, reply_markup=kb)


async def has_pending(msg: Message) -> bool:
    uid = msg.from_user.id
    st = pending.get(uid)
    if not st or not msg.text:
        return False
    if time.time() - st["ts"] > 900 or msg.text.startswith("/") or msg.text in NAV_TEXTS:
        pending.pop(uid, None)
        return False
    return True


@dp.message(F.text, has_pending)
async def on_pending(msg: Message):
    st = pending.get(msg.from_user.id)
    fn = ACTIONS.get(st["action"]) if st else None
    if not fn:
        clear_state(msg.from_user.id)
        return
    st["ts"] = time.time()
    await fn(msg, st)


def parse_bet(text: str, balance: int):
    t = (text or "").replace("💰", "").strip().lower()
    if t in ("всё", "все", "all"):
        return balance
    return to_int(t)


# ==================== ОСНОВНЫЕ КОМАНДЫ ====================
async def home(msg: Message, text: str = "🏠 Главное меню"):
    clear_state(msg.from_user.id)
    await say(msg, text, main_menu())


@dp.message(Command("start"))
async def start_cmd(msg: Message):
    clear_state(msg.from_user.id)
    user = await get_user(msg.from_user.id, msg.from_user.full_name)
    await msg.answer(f"❄️ {BOT_NAME} v{VERSION}\n👤 {msg.from_user.full_name}\n💰 {fmt(user['balance'])} ❄️\n"
                     f"🆔 {msg.from_user.id}\n\nВсё управляется кнопками внизу 👇", reply_markup=main_menu())


async def help_text(msg: Message) -> str:
    rank = await get_user_rank(msg.from_user.id, msg.chat.id if msg.chat.type != "private" else None)
    text = (f"❄️ {BOT_NAME}\n🏆 Ваш ранг: {RANKS[rank]['name']}\n\n"
            "Всё работает кнопками — команды писать не нужно:\n"
            "👤 Профиль — ник, титул, значок, инвентарь\n"
            "💑 Брак и 🎭 РП — отношения и действия с игроками\n"
            "🛒 Магазин — VIP, бусты, косметика, питомцы\n"
            "🎮 Игры — слоты, рулетка, кейсы, дуэли, колесо удачи\n"
            "💼 Экономика — дейли, работа, банк, кредиты, переводы\n"
            "🏰 Кланы и 🐾 Питомцы\n"
            "🎫 Поддержка — тикеты для админов\n")
    if rank >= 2:
        text += "\n⚔️ В группе (ответом на сообщение): /ban /kick /mute /warn /clear\n"
    return text


@dp.message(Command("help"))
async def help_cmd(msg: Message):
    await say(msg, await help_text(msg), main_menu())


@dp.message(F.text == "❓ Помощь")
async def m_help(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, await help_text(msg), main_menu())


@dp.message(F.text.in_({BACK, CANCEL}))
async def m_back(msg: Message):
    await home(msg)


# ==================== ПРОФИЛЬ ====================
async def profile_text(uid: int) -> str:
    u = await get_user(uid)
    vip = await effect_until(uid, "vip")
    badge = (u["badge"] + " ") if u["badge"] else ""
    title = f" «{u['title']}»" if u["title"] else ""
    async with db.execute("SELECT balance FROM bank WHERE user_id = ?", (uid,)) as c:
        r = await c.fetchone()
    bank = r["balance"] if r else 0
    partners = []
    for pid in (u["marry_id"], u["marry_id2"]):
        if pid:
            partners.append(dn(await get_user(pid)))
    clan_line = "—"
    if u["clan_id"]:
        async with db.execute("SELECT name, tag FROM clans WHERE id = ?", (u["clan_id"],)) as c:
            cl = await c.fetchone()
        if cl:
            clan_line = f"{cl['name']} [{cl['tag']}]"
    pet = await get_pet(uid)
    xp = u["xp"] or 0
    lines = [f"👤 {badge}{dn(u)}{title}" + (" 💎" if vip else ""),
             f"🆔 {uid}",
             "━━━━━━━━━━━━━━",
             f"💰 Кошелёк: {fmt(u['balance'])} ❄️",
             f"🏦 В банке: {fmt(bank)} ❄️",
             f"📊 Уровень {u['level'] or 1}  {bar(xp % 200, 200)} {xp % 200}/200",
             f"💍 Брак: {', '.join(partners) if partners else 'не в браке'}",
             f"🏰 Клан: {clan_line}"]
    if pet:
        lines.append(f"🐾 Питомец: {pet['type']} «{pet['name']}» (ур. {pet['level']})")
    if vip:
        lines.append(f"💎 VIP до {vip.strftime('%d.%m.%Y %H:%M')}")
    if u["bio"]:
        lines.append(f"📝 {u['bio']}")
    return "\n".join(lines)


@dp.message(F.text == "👤 Профиль")
async def m_profile(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.reply_to_message.from_user.id if msg.reply_to_message else msg.from_user.id
    await say(msg, await profile_text(uid), profile_menu())


@dp.message(Command("profile"))
async def profile_cmd(msg: Message):
    await m_profile(msg)


@dp.message(F.text == "💰 Баланс")
async def m_balance(msg: Message):
    clear_state(msg.from_user.id)
    user = await get_user(msg.from_user.id)
    await say(msg, f"💰 Ваш баланс: {fmt(user['balance'])} ❄️", main_menu())


@dp.message(Command("balance"))
async def balance_cmd(msg: Message):
    await m_balance(msg)


@dp.message(F.text == "🏆 Ранги")
async def m_rank(msg: Message):
    clear_state(msg.from_user.id)
    rank = await get_user_rank(msg.from_user.id, msg.chat.id if msg.chat.type != "private" else None)
    text = f"🏆 Ваш ранг: {RANKS[rank]['name']}\n\nВсе ранги:\n"
    text += "\n".join(f"{RANKS[r]['name']}" for r in (5, 4, 3, 2, 1))
    await say(msg, text, main_menu())


@dp.message(F.text == "📊 Топ")
async def m_top_menu(msg: Message):
    clear_state(msg.from_user.id)
    await show_top(msg, "balance")


@dp.message(F.text == "💰 Богачи")
async def m_top_rich(msg: Message):
    await show_top(msg, "balance")


@dp.message(F.text == "🏅 Уровни")
async def m_top_lvl(msg: Message):
    await show_top(msg, "xp")


@dp.message(Command("top"))
async def top_cmd(msg: Message):
    await show_top(msg, "balance")


async def show_top(msg: Message, by: str):
    col = "balance" if by == "balance" else "xp"
    async with db.execute(f"SELECT * FROM users ORDER BY {col} DESC LIMIT 10") as c:
        rows = await c.fetchall()
    medals = ["🥇", "🥈", "🥉"]
    head = "📊 ТОП БОГАЧЕЙ" if by == "balance" else "📊 ТОП ПО УРОВНЮ"
    lines = [head, ""]
    for i, u in enumerate(rows, 1):
        mark = medals[i - 1] if i <= 3 else f"{i}."
        badge = (u["badge"] + " ") if u["badge"] else ""
        val = f"{fmt(u['balance'])} ❄️" if by == "balance" else f"ур. {u['level'] or 1} ({fmt(u['xp'] or 0)} XP)"
        lines.append(f"{mark} {badge}{dn(u)} — {val}")
    await say(msg, "\n".join(lines), top_menu())


# ==================== ПРОФИЛЬ: СМЕНА НИКА / БИО / ТИТУЛА / ЗНАЧКА ====================
TOKEN_INFO = {
    "nick":  ("✏️ Введите новый ник (до 32 символов):", 32),
    "bio":   ("📝 Напишите о себе (до 100 символов):", 100),
    "title": ("🏷 Введите титул (до 20 символов):", 20),
}


async def start_token_use(msg: Message, key: str):
    uid = msg.from_user.id
    if await inv_get(uid, key) <= 0:
        await say(msg, f"❌ Это платная услуга: «{SHOP[key]['name']}» — {fmt(SHOP[key]['price'])} ❄️.\n"
                       "Купить можно в магазине 👇", shop_menu())
        return
    set_state(uid, "token_" + key)
    if key == "badge":
        rows = [BADGES[i:i + 3] for i in range(0, len(BADGES), 3)]
        await say(msg, "🎖 Выберите значок:", K(*rows, [CANCEL]))
    else:
        await say(msg, TOKEN_INFO[key][0], K([CANCEL]))


@dp.message(F.text == "✏️ Сменить ник")
async def m_setnick(msg: Message): await start_token_use(msg, "nick")


@dp.message(F.text == "📝 Сменить био")
async def m_setbio(msg: Message): await start_token_use(msg, "bio")


@dp.message(F.text == "🏷 Сменить титул")
async def m_settitle(msg: Message): await start_token_use(msg, "title")


@dp.message(F.text == "🎖 Сменить значок")
async def m_setbadge(msg: Message): await start_token_use(msg, "badge")


async def _apply_token(msg: Message, st, key: str):
    uid = msg.from_user.id
    text = (msg.text or "").strip()
    if key == "badge":
        if text not in BADGES:
            await say(msg, "❌ Выберите значок кнопкой ниже.")
            return
        value, col = text, "badge"
    else:
        limit = TOKEN_INFO[key][1]
        if not text or len(text) > limit:
            await say(msg, f"❌ От 1 до {limit} символов. Попробуйте ещё раз.")
            return
        value, col = text, {"nick": "nickname", "bio": "bio", "title": "title"}[key]
    if not await inv_take(uid, key):
        clear_state(uid)
        await say(msg, "❌ Нет оплаченной услуги.", shop_menu())
        return
    await db.execute(f"UPDATE users SET {col} = ? WHERE user_id = ?", (value, uid))
    await db.commit()
    clear_state(uid)
    await say(msg, "✅ Готово!\n\n" + await profile_text(uid), profile_menu())


for _k in ("nick", "bio", "title", "badge"):
    ACTIONS["token_" + _k] = (lambda k: (lambda msg, st: _apply_token(msg, st, k)))(_k)


# ==================== МАГАЗИН ====================
@dp.message(F.text == "🛒 Магазин")
async def m_shop(msg: Message):
    clear_state(msg.from_user.id)
    await show_shop(msg)


@dp.message(Command("shop"))
async def shop_cmd(msg: Message):
    await m_shop(msg)


@dp.message(F.text == BACK_SHOP)
async def m_back_shop(msg: Message):
    await show_shop(msg)


async def show_shop(msg: Message):
    user = await get_user(msg.from_user.id)
    await say(msg, f"🛒 МАГАЗИН\n💰 Ваш баланс: {fmt(user['balance'])} ❄️\n\n"
                   "💎 Статусы — VIP с бонусами\n✨ Внешний вид — ник, био, титул, значок\n"
                   "⚡ Бусты — щит, отмычка, удача, сбросы\n🐾 Для питомцев — питомцы и корм\n\n"
                   "Выберите раздел 👇", shop_menu())


@dp.message(F.text.in_(set(CAT_BY_LABEL)))
async def m_shop_cat(msg: Message):
    cat = CAT_BY_LABEL[msg.text]
    await show_cat(msg, cat)


async def show_cat(msg: Message, cat: str):
    clear_state(msg.from_user.id)
    user = await get_user(msg.from_user.id)
    lines = [f"{SHOP_CATS[cat][0]}", f"💰 Баланс: {fmt(user['balance'])} ❄️", ""]
    for k in SHOP_CATS[cat][1]:
        lines.append(f"{item_label(k)}\n    {SHOP[k]['desc']}")
    lines.append("\nНажмите на товар, чтобы посмотреть и купить 👇")
    await say(msg, "\n".join(lines), cat_menu(cat))


@dp.message(F.text.in_(set(ITEM_BY_LABEL)))
async def m_shop_item(msg: Message):
    key = ITEM_BY_LABEL[msg.text]
    it = SHOP[key]
    user = await get_user(msg.from_user.id)
    set_state(msg.from_user.id, "shop_confirm", item=key)
    await say(msg, f"{it['emoji']} {it['name']}\n\n{it['desc']}\n\n💵 Цена: {fmt(it['price'])} ❄️\n"
                   f"💰 У вас: {fmt(user['balance'])} ❄️", K(["✅ Купить"], [BACK_SHOP]))


@action("shop_confirm")
async def act_shop_confirm(msg: Message, st):
    if msg.text != "✅ Купить":
        await say(msg, "Нажмите «✅ Купить» или вернитесь в магазин.")
        return
    clear_state(msg.from_user.id)
    await buy_item(msg, st["item"])


async def buy_item(msg: Message, key: str):
    uid = msg.from_user.id
    it = SHOP[key]
    u = await get_user(uid)
    cat = next(c for c, v in SHOP_CATS.items() if key in v[1])

    # проверки до списания денег
    if "pet" in it and await get_pet(uid):
        await say(msg, "❌ У вас уже есть питомец.", cat_menu(cat)); return
    if key == "work_reset":
        last = parse_dt(u["work_cooldown"])
        if not last or (datetime.now() - last).total_seconds() >= 7200:
            await say(msg, "ℹ️ Вы и так можете работать — сброс не нужен.", cat_menu(cat)); return
    if key == "daily_reset":
        last = parse_dt(u["last_daily"])
        if not last or (datetime.now() - last).total_seconds() >= 86400:
            await say(msg, "ℹ️ Дейли уже доступен — сброс не нужен.", cat_menu(cat)); return
    if not await spend(uid, it["price"]):
        await say(msg, f"❌ Не хватает ❄️. Нужно {fmt(it['price'])}, у вас {fmt(u['balance'])}.", cat_menu(cat)); return

    if key in ("vip", "vip30"):
        until = await effect_add(uid, "vip", 24 * (7 if key == "vip" else 30))
        await say(msg, f"✅ VIP активен до {until.strftime('%d.%m.%Y %H:%M')}! 💎", cat_menu(cat))
    elif key in ("nick", "bio", "title", "badge"):
        await inv_add(uid, key)
        await say(msg, f"✅ Куплено: {it['name']}.")
        await start_token_use(msg, key)
    elif key == "shield":
        until = await effect_add(uid, "shield", 24)
        await say(msg, f"🛡 Щит активен до {until.strftime('%d.%m %H:%M')}", cat_menu(cat))
    elif key == "luck":
        until = await effect_add(uid, "luck", 6)
        await say(msg, f"🍀 Удача с вами до {until.strftime('%d.%m %H:%M')}", cat_menu(cat))
    elif key == "lockpick":
        await inv_add(uid, "lockpick")
        await say(msg, "🗝 Отмычка в инвентаре — применится сама при ограблении.", cat_menu(cat))
    elif key == "work_reset":
        await db.execute("UPDATE users SET work_cooldown = NULL WHERE user_id = ?", (uid,))
        await db.commit()
        await say(msg, "⏱ Готово! Можно снова на работу 💼", cat_menu(cat))
    elif key == "daily_reset":
        await db.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", ((datetime.now() - timedelta(hours=25)).isoformat(), uid))
        await db.commit()
        await say(msg, "🔄 Готово! Забирайте дейли 🎁", cat_menu(cat))
    elif key == "pet_food":
        await inv_add(uid, "pet_food", 3)
        await say(msg, "🍖 +3 порции премиум-корма в инвентаре.", cat_menu(cat))
    elif "pet" in it:
        await db.execute("INSERT INTO pets (owner_id, type, name, created) VALUES (?, ?, ?, ?)",
                         (uid, it["pet"], it["pet"].split(" ", 1)[1], datetime.now().isoformat()))
        await db.commit()
        await say(msg, f"✅ Вы купили {it['pet']}! Загляните в 🐾 Питомцы.", cat_menu(cat))


@dp.message(F.text == "🎒 Инвентарь")
async def m_inventory(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    lines = ["🎒 ИНВЕНТАРЬ", ""]
    empty = True
    for key in ("nick", "bio", "title", "badge", "lockpick", "pet_food"):
        qty = await inv_get(uid, key)
        if qty > 0:
            empty = False
            extra = " — применить: Профиль → «Сменить…»" if key in TOKEN_INFO or key == "badge" else ""
            lines.append(f"{SHOP[key]['emoji']} {SHOP[key]['name']} × {qty}{extra}")
    for key, name in (("vip", "💎 VIP"), ("shield", "🛡 Щит"), ("luck", "🍀 Удача")):
        until = await effect_until(uid, key)
        if until:
            empty = False
            lines.append(f"{name}: ещё {left_str((until - datetime.now()).total_seconds())}")
    if empty:
        lines.append("Пока пусто. Загляните в 🛒 Магазин!")
    await say(msg, "\n".join(lines), shop_menu())


# ==================== ЭКОНОМИКА ====================
JOBS = [("👨‍💻 Программист", 50, 200), ("👷 Строитель", 30, 150), ("🚚 Курьер", 40, 180),
        ("🧑‍🍳 Повар", 35, 160), ("🎣 Рыбак", 20, 220)]


@dp.message(F.text.in_({"💼 Экономика", BACK_ECO}))
async def m_economy(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, "💼 ЭКОНОМИКА\nВыберите действие 👇", economy_menu())


@dp.message(F.text == "🎁 Дейли")
async def m_daily(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    u = await get_user(uid)
    now = datetime.now()
    last = parse_dt(u["last_daily"])
    if last and (now - last).total_seconds() < 86400:
        await say(msg, f"⏳ Следующий дейли через {left_str(86400 - (now - last).total_seconds())}", economy_menu())
        return
    streak = (u["daily_streak"] or 0) + 1 if last and (now - last).total_seconds() < 172800 else 1
    streak = min(streak, MAX_STREAK)
    bonus = DAILY_BONUS_BASE + (streak - 1) * DAILY_STREAK_BONUS
    vip = await effect_active(uid, "vip")
    if vip:
        bonus = int(bonus * 1.5)
    await db.execute("UPDATE users SET balance = balance + ?, daily_streak = ?, last_daily = ? WHERE user_id = ?",
                     (bonus, streak, now.isoformat(), uid))
    await db.commit()
    await add_xp(uid, 10)
    await say(msg, f"🎁 +{fmt(bonus)} ❄️" + (" (VIP +50%)" if vip else "") +
              f"\n🔥 Стрик: {streak}/{MAX_STREAK}\nВозвращайтесь через 24 часа!", economy_menu())


@dp.message(Command("daily"))
async def daily_cmd(msg: Message):
    await m_daily(msg)


@dp.message(F.text == "💼 Работа")
async def m_work(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    u = await get_user(uid)
    last = parse_dt(u["work_cooldown"])
    if last and (datetime.now() - last).total_seconds() < 7200:
        await say(msg, f"⏳ Отдыхайте ещё {left_str(7200 - (datetime.now() - last).total_seconds())}\n"
                       "Подсказка: «⏱ Сброс Работы» есть в магазине.", economy_menu())
        return
    job, mn, mx = random.choice(JOBS)
    mult = 1 + 0.02 * ((u["level"] or 1) - 1)
    if await effect_active(uid, "vip"):
        mult += 0.25
    if await effect_active(uid, "luck"):
        mult += 0.10
    earned = int(random.randint(mn, mx) * mult)
    await db.execute("UPDATE users SET balance = balance + ?, work_cooldown = ? WHERE user_id = ?",
                     (earned, datetime.now().isoformat(), uid))
    await db.commit()
    await add_xp(uid, 5)
    await say(msg, f"💼 {job}\n💰 +{fmt(earned)} ❄️", economy_menu())


@dp.message(Command("work"))
async def work_cmd(msg: Message):
    await m_work(msg)


# ----- перевод -----
@dp.message(F.text == "💸 Перевод")
async def m_pay(msg: Message):
    set_state(msg.from_user.id, "pay_target")
    await say(msg, "💸 Кому перевести?\nОтправьте @username или ник игрока.", K([CANCEL]))


@action("pay_target")
async def act_pay_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Он должен хотя бы раз написать боту.\nПопробуйте ещё раз:", K([CANCEL]))
        return
    if target["user_id"] == msg.from_user.id:
        await say(msg, "❌ Нельзя переводить самому себе.", K([CANCEL]))
        return
    me = await get_user(msg.from_user.id)
    set_state(msg.from_user.id, "pay_amount", target=target["user_id"])
    await say(msg, f"Получатель: {dn(target)}\nНалог: {int(TRANSFER_TAX * 100)}%\n💰 У вас: {fmt(me['balance'])} ❄️\n\nСколько отправить?",
              bet_kb(BACK_ECO))


@action("pay_amount")
async def act_pay_amount(msg: Message, st):
    uid = msg.from_user.id
    me = await get_user(uid)
    amount = parse_bet(msg.text, me["balance"])
    if amount is None or amount < 1:
        await say(msg, "❌ Введите число или выберите кнопку.")
        return
    if not await spend(uid, amount):
        await say(msg, f"❌ Недостаточно средств. У вас {fmt(me['balance'])} ❄️")
        return
    tax = int(amount * TRANSFER_TAX)
    receive = amount - tax
    await give(st["target"], receive)
    clear_state(uid)
    target = await get_user(st["target"])
    await say(msg, f"💸 Перевод для {dn(target)}\nСумма: {fmt(amount)} ❄️\nНалог: {fmt(tax)} ❄️\nПолучено: {fmt(receive)} ❄️", economy_menu())
    await notify(st["target"], f"💸 {dn(me)} отправил(а) вам {fmt(receive)} ❄️")


# ----- банк -----
async def bank_balance(uid: int) -> int:
    async with db.execute("SELECT balance FROM bank WHERE user_id = ?", (uid,)) as c:
        r = await c.fetchone()
    return r["balance"] if r else 0


async def show_bank(msg: Message):
    u = await get_user(msg.from_user.id)
    await say(msg, f"🏦 БАНК\n🏦 В банке: {fmt(await bank_balance(msg.from_user.id))} ❄️\n💰 В кошельке: {fmt(u['balance'])} ❄️\n\n"
                   f"📈 Проценты: {int(BANK_INTEREST * 100)}% раз в сутки (максимум 5 000 ❄️)", bank_menu())


@dp.message(F.text == "🏦 Банк")
async def m_bank(msg: Message):
    clear_state(msg.from_user.id)
    await show_bank(msg)


@dp.message(F.text == "💰 Внести")
async def m_bank_dep(msg: Message):
    set_state(msg.from_user.id, "bank_dep")
    await say(msg, "💰 Сколько внести в банк?", bet_kb(BACK_ECO))


@dp.message(F.text == "💵 Снять")
async def m_bank_wd(msg: Message):
    set_state(msg.from_user.id, "bank_wd")
    await say(msg, f"💵 Сколько снять? В банке: {fmt(await bank_balance(msg.from_user.id))} ❄️", bet_kb(BACK_ECO))


@action("bank_dep")
async def act_bank_dep(msg: Message, st):
    uid = msg.from_user.id
    u = await get_user(uid)
    amount = parse_bet(msg.text, u["balance"])
    if amount is None or amount < 1:
        await say(msg, "❌ Введите число или выберите кнопку.")
        return
    if not await spend(uid, amount):
        await say(msg, f"❌ Недостаточно средств. У вас {fmt(u['balance'])} ❄️")
        return
    await db.execute("INSERT INTO bank (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?",
                     (uid, amount, amount))
    await db.commit()
    clear_state(uid)
    await say(msg, f"✅ Внесено {fmt(amount)} ❄️")
    await show_bank(msg)


@action("bank_wd")
async def act_bank_wd(msg: Message, st):
    uid = msg.from_user.id
    bank = await bank_balance(uid)
    amount = parse_bet(msg.text, bank)
    if amount is None or amount < 1:
        await say(msg, "❌ Введите число или выберите кнопку.")
        return
    cur = await db.execute("UPDATE bank SET balance = balance - ? WHERE user_id = ? AND balance >= ?", (amount, uid, amount))
    if cur.rowcount != 1:
        await db.commit()
        await say(msg, f"❌ В банке только {fmt(bank)} ❄️")
        return
    await give(uid, amount)
    clear_state(uid)
    await say(msg, f"✅ Снято {fmt(amount)} ❄️")
    await show_bank(msg)


@dp.message(F.text == "📈 Получить проценты")
async def m_interest(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    until = await effect_until(uid, "bank_interest")
    if until:
        await say(msg, f"⏳ Проценты можно получить через {left_str((until - datetime.now()).total_seconds())}", bank_menu())
        return
    bank = await bank_balance(uid)
    if bank < 100:
        await say(msg, "❌ Для процентов нужно минимум 100 ❄️ в банке.", bank_menu())
        return
    gain = min(5000, int(bank * BANK_INTEREST))
    await db.execute("UPDATE bank SET balance = balance + ? WHERE user_id = ?", (gain, uid))
    await db.commit()
    await effect_add(uid, "bank_interest", 24)
    await say(msg, f"📈 Начислено {fmt(gain)} ❄️ процентов прямо на счёт!", bank_menu())


# ----- кредит -----
@dp.message(F.text == "💳 Кредит")
async def m_loan(msg: Message):
    clear_state(msg.from_user.id)
    u = await get_user(msg.from_user.id)
    debt = u["loan_amount"] or 0
    if debt:
        total = debt + int(debt * LOAN_INTEREST)
        text = f"💳 КРЕДИТ\nВаш долг: {fmt(debt)} ❄️\nК возврату: {fmt(total)} ❄️"
    else:
        text = f"💳 КРЕДИТ\nДолга нет.\nМожно взять от 100 до 10 000 ❄️ под {int(LOAN_INTEREST * 100)}%."
    await say(msg, text, loan_menu())


@dp.message(F.text == "💳 Взять кредит")
async def m_loan_take(msg: Message):
    u = await get_user(msg.from_user.id)
    if u["loan_amount"]:
        await say(msg, "❌ Сначала погасите текущий кредит.", loan_menu())
        return
    set_state(msg.from_user.id, "loan_take")
    await say(msg, "💳 Сколько взять? (100 – 10 000 ❄️)", loan_kb())


@action("loan_take")
async def act_loan_take(msg: Message, st):
    uid = msg.from_user.id
    amount = to_int((msg.text or "").replace("💰", ""))
    if amount is None or amount < 100 or amount > 10000:
        await say(msg, "❌ От 100 до 10 000 ❄️. Выберите кнопку или введите число.")
        return
    await db.execute("UPDATE users SET balance = balance + ?, loan_amount = ?, loan_date = ? WHERE user_id = ?",
                     (amount, amount, datetime.now().isoformat(), uid))
    await db.commit()
    clear_state(uid)
    total = amount + int(amount * LOAN_INTEREST)
    await say(msg, f"✅ Кредит {fmt(amount)} ❄️ выдан.\nВернуть нужно {fmt(total)} ❄️.", loan_menu())


@dp.message(F.text == "✅ Погасить кредит")
async def m_loan_pay(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    u = await get_user(uid)
    debt = u["loan_amount"] or 0
    if not debt:
        await say(msg, "✅ У вас нет кредита.", loan_menu())
        return
    total = debt + int(debt * LOAN_INTEREST)
    if not await spend(uid, total):
        await say(msg, f"❌ Нужно {fmt(total)} ❄️, у вас {fmt(u['balance'])}.", loan_menu())
        return
    await db.execute("UPDATE users SET loan_amount = 0, loan_date = NULL WHERE user_id = ?", (uid,))
    await db.commit()
    await say(msg, f"✅ Кредит погашен: {fmt(total)} ❄️", loan_menu())


# ----- ограбление -----
@dp.message(F.text == "🦹 Грабеж")
async def m_rob(msg: Message):
    clear_state(msg.from_user.id)
    if msg.reply_to_message and msg.reply_to_message.from_user:
        await do_rob(msg, msg.reply_to_message.from_user.id)
        return
    set_state(msg.from_user.id, "rob_target")
    await say(msg, "🦹 Кого грабим?\nОтправьте @username или ник жертвы.", K([CANCEL]))


@action("rob_target")
async def act_rob_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Попробуйте ещё раз:", K([CANCEL]))
        return
    await do_rob(msg, target["user_id"])


async def do_rob(msg: Message, victim_id: int):
    uid = msg.from_user.id
    clear_state(uid)
    if victim_id == uid:
        await say(msg, "❌ Нельзя грабить самого себя!", economy_menu()); return
    robber = await get_user(uid)
    last = parse_dt(robber["rob_cooldown"])
    if last and (datetime.now() - last).total_seconds() < ROB_COOLDOWN_HOURS * 3600:
        left = ROB_COOLDOWN_HOURS * 3600 - (datetime.now() - last).total_seconds()
        await say(msg, f"⏳ Грабить можно снова через {left_str(left)}", economy_menu()); return
    victim = await get_user(victim_id)
    if await effect_active(victim_id, "shield"):
        await say(msg, f"🛡 У {dn(victim)} активен щит — ограбление невозможно.", economy_menu()); return
    if victim["balance"] < 100:
        await say(msg, f"❌ У {dn(victim)} меньше 100 ❄️ — не стоит рисковать.", economy_menu()); return
    await db.execute("UPDATE users SET rob_cooldown = ? WHERE user_id = ?", (datetime.now().isoformat(), uid))
    await db.commit()
    chance = ROB_SUCCESS_CHANCE
    if await inv_take(uid, "lockpick"):
        chance += 0.25
    if await effect_active(uid, "luck"):
        chance += 0.10
    if random.random() < chance:
        cap = max(50, min(ROB_MAX_AMOUNT, victim["balance"] // 2))
        stolen = random.randint(50, cap)
        if await spend(victim_id, stolen):
            await give(uid, stolen)
            await say(msg, f"🦹 Успех! Вы украли {fmt(stolen)} ❄️ у {dn(victim)}", economy_menu())
            await notify(victim_id, f"🦹 {dn(robber)} ограбил(а) вас на {fmt(stolen)} ❄️!\nЩит в магазине защитит на сутки 🛡")
        else:
            await say(msg, "😅 Жертва успела потратить деньги — вы ушли ни с чем.", economy_menu())
    else:
        fine = random.randint(100, 500)
        fine = min(fine, robber["balance"])
        if fine:
            await spend(uid, fine)
        await say(msg, f"🚔 Провал! Штраф: {fmt(fine)} ❄️", economy_menu())


# ----- промокоды -----
@dp.message(F.text == "🎟 Промокод")
async def m_promo_use(msg: Message):
    set_state(msg.from_user.id, "promo_use")
    await say(msg, "🎟 Введите промокод:", K([CANCEL]))


async def apply_promo(msg: Message, code: str):
    uid = msg.from_user.id
    code = code.strip().upper()
    async with db.execute("SELECT reward, uses, used_by FROM promocodes WHERE code = ?", (code,)) as c:
        promo = await c.fetchone()
    if not promo:
        await say(msg, "❌ Промокод не найден.", economy_menu()); return
    used = json.loads(promo["used_by"]) if promo["used_by"] else []
    if str(uid) in used:
        await say(msg, "❌ Вы уже использовали этот промокод.", economy_menu()); return
    if promo["uses"] <= 0:
        await say(msg, "❌ Промокод закончился.", economy_menu()); return
    used.append(str(uid))
    await db.execute("UPDATE promocodes SET uses = uses - 1, used_by = ? WHERE code = ?", (json.dumps(used), code))
    await db.commit()
    await give(uid, promo["reward"])
    await say(msg, f"🎉 Промокод активирован: +{fmt(promo['reward'])} ❄️", economy_menu())


@action("promo_use")
async def act_promo_use(msg: Message, st):
    clear_state(msg.from_user.id)
    await apply_promo(msg, msg.text)


@dp.message(Command("use"))
async def use_cmd(msg: Message):
    parts = msg.text.split()
    if len(parts) < 2:
        await m_promo_use(msg)
        return
    await apply_promo(msg, parts[1])


# ==================== ИГРЫ ====================
@dp.message(F.text == "🎮 Игры")
async def m_games(msg: Message):
    clear_state(msg.from_user.id)
    u = await get_user(msg.from_user.id)
    await say(msg, f"🎮 ИГРЫ\n💰 Баланс: {fmt(u['balance'])} ❄️\nВыберите игру 👇", games_menu())


async def take_bet(msg: Message, bet, kb) -> bool:
    if bet is None or bet < MIN_BET:
        await say(msg, f"❌ Минимальная ставка {MIN_BET} ❄️. Выберите кнопку или введите число.", kb)
        return False
    if not await spend(msg.from_user.id, bet):
        u = await get_user(msg.from_user.id)
        await say(msg, f"❌ Недостаточно средств. У вас {fmt(u['balance'])} ❄️", kb)
        return False
    return True


async def balance_line(uid: int) -> str:
    return f"💰 Баланс: {fmt((await get_user(uid))['balance'])} ❄️"


# ----- слоты -----
@dp.message(F.text == "🎰 Слоты")
async def m_slots(msg: Message):
    set_state(msg.from_user.id, "slots")
    await say(msg, f"🎰 СЛОТЫ\nТри одинаковых — большой выигрыш (до ×50), две — ×1.5.\n{await balance_line(msg.from_user.id)}\n\nВыберите ставку:", bet_kb())


@action("slots")
async def act_slots(msg: Message, st):
    uid = msg.from_user.id
    bet = parse_bet(msg.text, (await get_user(uid))["balance"])
    if not await take_bet(msg, bet, bet_kb()):
        return
    r = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    if r[0] == r[1] == r[2]:
        payout, text = bet * SLOT_PAYOUTS[r[0]], "🎉 ДЖЕКПОТ!"
    elif len(set(r)) == 2:
        payout, text = int(bet * 1.5), "✨ Пара!"
    else:
        payout, text = 0, "😢 Не повезло"
    if payout:
        await give(uid, payout)
    await add_xp(uid, 2)
    net = payout - bet
    await say(msg, f"🎰 [ {r[0]} | {r[1]} | {r[2]} ]\n{text} ({'+' if net >= 0 else ''}{fmt(net)} ❄️)\n{await balance_line(uid)}", bet_kb())


# ----- рулетка -----
R_RED, R_BLACK, R_GREEN, R_NUM = "🔴 Красное ×2", "⚫ Чёрное ×2", "🟢 Зеро ×36", "🔢 Число ×36"


@dp.message(F.text == "🎲 Рулетка")
async def m_roulette(msg: Message):
    set_state(msg.from_user.id, "roulette_pick")
    await say(msg, "🎲 РУЛЕТКА\nНа что ставим?", K([R_RED, R_BLACK], [R_GREEN, R_NUM], [BACK]))


@action("roulette_pick")
async def act_roulette_pick(msg: Message, st):
    uid = msg.from_user.id
    pick = {R_RED: "red", R_BLACK: "black", R_GREEN: "green"}.get(msg.text)
    if msg.text == R_NUM:
        set_state(uid, "roulette_number")
        await say(msg, "🔢 Введите число от 0 до 36:", K([BACK]))
    elif pick:
        set_state(uid, "roulette_bet", choice=pick)
        await say(msg, f"{await balance_line(uid)}\nВаша ставка:", bet_kb())
    else:
        await say(msg, "Выберите вариант кнопкой 👇")


@action("roulette_number")
async def act_roulette_number(msg: Message, st):
    n = to_int(msg.text)
    if n is None or not 0 <= n <= 36:
        await say(msg, "❌ Введите число от 0 до 36.")
        return
    set_state(msg.from_user.id, "roulette_bet", choice=str(n))
    await say(msg, f"Ставка на число {n} (×36).\n{await balance_line(msg.from_user.id)}\nВаша ставка:", bet_kb())


@action("roulette_bet")
async def act_roulette_bet(msg: Message, st):
    uid = msg.from_user.id
    bet = parse_bet(msg.text, (await get_user(uid))["balance"])
    if not await take_bet(msg, bet, bet_kb()):
        return
    number = random.randint(0, 36)
    color = "green" if number == 0 else ("red" if number in ROULETTE_RED else "black")
    icon = {"green": "🟢", "red": "🔴", "black": "⚫"}[color]
    choice = st["choice"]
    payout = 0
    if choice.isdigit() and int(choice) == number:
        payout = bet * 36
    elif choice == color:
        payout = bet * (36 if color == "green" else 2)
    if payout:
        await give(uid, payout)
    await add_xp(uid, 2)
    net = payout - bet
    res = f"🎉 Выигрыш {'+' if net >= 0 else ''}{fmt(net)} ❄️" if payout else f"😢 Проигрыш −{fmt(bet)} ❄️"
    await say(msg, f"🎲 Выпало: {icon} {number}\n{res}\n{await balance_line(uid)}\n\nСтавьте снова или нажмите «Назад».", bet_kb())


# ----- монетка -----
C_HEADS, C_TAILS = "🦅 Орёл", "🪙 Решка"


@dp.message(F.text == "🪙 Монетка")
async def m_coin(msg: Message):
    set_state(msg.from_user.id, "coin_pick")
    await say(msg, "🪙 МОНЕТКА\nВыберите сторону (выигрыш ×1.95):", K([C_HEADS, C_TAILS], [BACK]))


@action("coin_pick")
async def act_coin_pick(msg: Message, st):
    if msg.text not in (C_HEADS, C_TAILS):
        await say(msg, "Выберите сторону кнопкой 👇")
        return
    set_state(msg.from_user.id, "coin_bet", side=msg.text)
    await say(msg, f"Вы выбрали: {msg.text}\n{await balance_line(msg.from_user.id)}\nВаша ставка:", bet_kb())


@action("coin_bet")
async def act_coin_bet(msg: Message, st):
    uid = msg.from_user.id
    bet = parse_bet(msg.text, (await get_user(uid))["balance"])
    if not await take_bet(msg, bet, bet_kb()):
        return
    result = random.choice([C_HEADS, C_TAILS])
    if result == st["side"]:
        payout = int(bet * 1.95)
        await give(uid, payout)
        text = f"🎉 Угадали! +{fmt(payout - bet)} ❄️"
    else:
        text = f"😢 Не угадали. −{fmt(bet)} ❄️"
    await add_xp(uid, 2)
    await say(msg, f"Выпало: {result}\n{text}\n{await balance_line(uid)}", bet_kb())


# ----- камень-ножницы-бумага -----
RPS_CHOICES = ["🪨 Камень", "✂️ Ножницы", "📄 Бумага"]


@dp.message(F.text == "🎯 КНБ")
async def m_rps(msg: Message):
    set_state(msg.from_user.id, "rps")
    await say(msg, "🎯 КАМЕНЬ · НОЖНИЦЫ · БУМАГА\nИграем на интерес, ставок нет. Ваш ход:", K(RPS_CHOICES, [BACK]))


@action("rps")
async def act_rps(msg: Message, st):
    if msg.text not in RPS_CHOICES:
        await say(msg, "Выберите ход кнопкой 👇")
        return
    me, bot_choice = RPS_CHOICES.index(msg.text), random.randrange(3)
    if me == bot_choice:
        res = "🤝 Ничья!"
    elif (me - bot_choice) % 3 == 1:
        res = "🎉 Вы выиграли!"
    else:
        res = "😢 Вы проиграли"
    await say(msg, f"Вы: {RPS_CHOICES[me]}\nБот: {RPS_CHOICES[bot_choice]}\n{res}", K(RPS_CHOICES, [BACK]))


# ----- кейсы -----
def cases_kb():
    return K(*[[label] for label in CASES], [BACK])


@dp.message(F.text == "📦 Кейсы")
async def m_cases(msg: Message):
    set_state(msg.from_user.id, "cases")
    await say(msg, f"📦 КЕЙСЫ\nОткройте кейс и посмотрите, что выпадет!\n{await balance_line(msg.from_user.id)}", cases_kb())


@action("cases")
async def act_cases(msg: Message, st):
    uid = msg.from_user.id
    if msg.text not in CASES:
        await say(msg, "Выберите кейс кнопкой 👇")
        return
    price, outcomes = CASES[msg.text]
    if not await take_bet(msg, price, cases_kb()):
        return
    win = random.choices([o[0] for o in outcomes], weights=[o[1] for o in outcomes])[0]
    if win and await effect_active(uid, "luck"):
        win = int(win * 1.15)
    if win:
        await give(uid, win)
    await add_xp(uid, 3)
    net = win - price
    await say(msg, f"📦 Вы открыли кейс за {fmt(price)} ❄️\n🎁 Выпало: {fmt(win)} ❄️ ({'+' if net >= 0 else ''}{fmt(net)})\n{await balance_line(uid)}", cases_kb())


# ----- колесо удачи -----
@dp.message(F.text == "🎡 Колесо удачи")
async def m_wheel(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    until = await effect_until(uid, "wheel")
    if until:
        await say(msg, f"⏳ Колесо снова крутится через {left_str((until - datetime.now()).total_seconds())}", games_menu())
        return
    prize = random.choices([p[0] for p in WHEEL_PRIZES], weights=[p[1] for p in WHEEL_PRIZES])[0]
    await give(uid, prize)
    await effect_add(uid, "wheel", 12)
    await say(msg, f"🎡 Колесо остановилось!\n🎁 Ваш приз: {fmt(prize)} ❄️\nСледующая попытка через 12 часов.", games_menu())


# ----- дуэль -----
@dp.message(F.text == "⚔️ Дуэль")
async def m_duel(msg: Message):
    set_state(msg.from_user.id, "duel_target")
    await say(msg, "⚔️ ДУЭЛЬ\nС кем сражаемся? Отправьте @username или ник соперника.", K([CANCEL]))


@action("duel_target")
async def act_duel_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Он должен хотя бы раз написать боту.\nПопробуйте ещё раз:", K([CANCEL]))
        return
    if target["user_id"] == msg.from_user.id:
        await say(msg, "❌ Нельзя вызвать самого себя.", K([CANCEL]))
        return
    set_state(msg.from_user.id, "duel_bet", target=target["user_id"])
    await say(msg, f"Соперник: {dn(target)} (💰 {fmt(target['balance'])} ❄️)\nСтавка? Победитель забирает всё.", bet_kb())


@action("duel_bet")
async def act_duel_bet(msg: Message, st):
    uid = msg.from_user.id
    me = await get_user(uid)
    target = await get_user(st["target"])
    bet = parse_bet(msg.text, me["balance"])
    if bet is None or bet < MIN_BET:
        await say(msg, f"❌ Минимальная ставка {MIN_BET} ❄️.")
        return
    if bet > me["balance"]:
        await say(msg, f"❌ У вас только {fmt(me['balance'])} ❄️.")
        return
    if bet > target["balance"]:
        await say(msg, f"❌ У соперника только {fmt(target['balance'])} ❄️ — ставка слишком велика.")
        return
    duel_requests[target["user_id"]] = {"from": uid, "bet": bet, "ts": time.time()}
    sent = await notify(target["user_id"], f"⚔️ {dn(me)} вызывает вас на дуэль!\nСтавка: {fmt(bet)} ❄️ с каждого.\nПринимаете?",
                        K([DUEL_YES], [DUEL_NO]))
    clear_state(uid)
    if not sent:
        duel_requests.pop(target["user_id"], None)
        await say(msg, f"❌ Не могу написать {dn(target)}: он ещё не запускал бота. Пусть откроет бота и нажмёт /start.", games_menu())
        return
    await say(msg, f"⚔️ Вызов отправлен игроку {dn(target)}. Ждём ответа 10 минут.", games_menu())


@dp.message(F.text == DUEL_YES)
async def m_duel_yes(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    req = duel_requests.pop(uid, None)
    if not req or time.time() - req["ts"] > 600:
        await say(msg, "⌛ Вызов не найден или уже устарел.", main_menu()); return
    ch, bet = req["from"], req["bet"]
    if not await spend(ch, bet):
        await say(msg, "❌ У вызвавшего уже не хватает ❄️ — дуэль отменена.", main_menu()); return
    if not await spend(uid, bet):
        await give(ch, bet)
        await say(msg, "❌ У вас не хватает ❄️ для этой ставки — дуэль отменена.", main_menu()); return
    winner, loser = random.choice([(ch, uid), (uid, ch)])
    await give(winner, bet * 2)
    w, l = await get_user(winner), await get_user(loser)
    text = f"⚔️ ДУЭЛЬ\n🏆 Победил: {dn(w)}\n💀 Проиграл: {dn(l)}\n💰 Выигрыш: {fmt(bet * 2)} ❄️"
    await say(msg, text, main_menu())
    await notify(ch, text, main_menu())


@dp.message(F.text == DUEL_NO)
async def m_duel_no(msg: Message):
    clear_state(msg.from_user.id)
    req = duel_requests.pop(msg.from_user.id, None)
    await say(msg, "❌ Вызов отклонён.", main_menu())
    if req:
        me = await get_user(msg.from_user.id)
        await notify(req["from"], f"❌ {dn(me)} отклонил(а) вашу дуэль.", main_menu())


# ==================== БРАК ====================
@dp.message(F.text == "💑 Брак")
async def m_marry(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, "💑 БРАК\nМожно иметь до двух партнёров.\nПредложение придёт избраннику в личные сообщения.", marry_menu())


async def partners_of(u):
    return [(slot, pid) for slot, pid in ((1, u["marry_id"]), (2, u["marry_id2"])) if pid]


@dp.message(F.text == "👫 Мои браки")
async def m_my_marriages(msg: Message):
    clear_state(msg.from_user.id)
    u = await get_user(msg.from_user.id)
    ps = await partners_of(u)
    if not ps:
        await say(msg, "💔 Вы не в браке.", marry_menu()); return
    names = [dn(await get_user(pid)) for _, pid in ps]
    await say(msg, "💍 Ваши партнёры:\n" + "\n".join(f"• {n}" for n in names), marry_menu())


@dp.message(F.text == "💍 Предложить брак")
async def m_marry_propose(msg: Message):
    u = await get_user(msg.from_user.id)
    if u["marry_id"] and u["marry_id2"]:
        await say(msg, "❌ У вас уже два партнёра!", marry_menu()); return
    set_state(msg.from_user.id, "marry_target")
    await say(msg, "💍 Кому делаем предложение? Отправьте @username или ник.", K([CANCEL]))


@action("marry_target")
async def act_marry_target(msg: Message, st):
    uid = msg.from_user.id
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Попробуйте ещё раз:", K([CANCEL])); return
    if target["user_id"] == uid:
        await say(msg, "❌ Нельзя на самом себе!", K([CANCEL])); return
    me = await get_user(uid)
    if target["user_id"] in (me["marry_id"], me["marry_id2"]):
        await say(msg, "💍 Вы уже в браке с этим игроком.", marry_menu()); clear_state(uid); return
    if target["marry_id"] and target["marry_id2"]:
        await say(msg, f"❌ У {dn(target)} уже два партнёра.", marry_menu()); clear_state(uid); return
    marry_requests[target["user_id"]] = {"from": uid, "ts": time.time()}
    sent = await notify(target["user_id"], f"💍 {dn(me)} предлагает вам брак!", K([MARRY_YES], [MARRY_NO]))
    clear_state(uid)
    if not sent:
        marry_requests.pop(target["user_id"], None)
        await say(msg, f"❌ Не могу написать {dn(target)}: он ещё не запускал бота.", marry_menu()); return
    await say(msg, f"💌 Предложение отправлено игроку {dn(target)}!", marry_menu())


@dp.message(F.text == MARRY_YES)
async def m_marry_yes(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    req = marry_requests.pop(uid, None)
    if not req or time.time() - req["ts"] > 86400:
        await say(msg, "⌛ Предложение не найдено или устарело.", main_menu()); return
    pid = req["from"]
    proposer, target = await get_user(pid), await get_user(uid)
    if (proposer["marry_id"] and proposer["marry_id2"]) or (target["marry_id"] and target["marry_id2"]):
        await say(msg, "❌ У одного из вас уже два партнёра.", main_menu()); return
    await db.execute(f"UPDATE users SET {'marry_id' if not proposer['marry_id'] else 'marry_id2'} = ? WHERE user_id = ?", (uid, pid))
    await db.execute(f"UPDATE users SET {'marry_id' if not target['marry_id'] else 'marry_id2'} = ? WHERE user_id = ?", (pid, uid))
    await db.commit()
    await say(msg, f"💍 ПОЗДРАВЛЯЕМ! Вы теперь в браке с {dn(proposer)}!", main_menu())
    await notify(pid, f"💍 {dn(target)} согласился(лась)! Поздравляем, вы в браке!", main_menu())


@dp.message(F.text == MARRY_NO)
async def m_marry_no(msg: Message):
    clear_state(msg.from_user.id)
    req = marry_requests.pop(msg.from_user.id, None)
    await say(msg, "💔 Вы отказали.", main_menu())
    if req:
        me = await get_user(msg.from_user.id)
        await notify(req["from"], f"💔 {dn(me)} отказал(а) вам.", main_menu())


async def do_divorce(msg: Message, partner_id: int):
    uid = msg.from_user.id
    clear_state(uid)
    for a, b in ((uid, partner_id), (partner_id, uid)):
        await db.execute("UPDATE users SET marry_id = NULL WHERE user_id = ? AND marry_id = ?", (a, b))
        await db.execute("UPDATE users SET marry_id2 = NULL WHERE user_id = ? AND marry_id2 = ?", (a, b))
    await db.commit()
    p = await get_user(partner_id)
    await say(msg, f"💔 Вы развелись с {dn(p)}.", marry_menu())
    me = await get_user(uid)
    await notify(partner_id, f"💔 {dn(me)} развёлся(лась) с вами.")


@dp.message(F.text == "💔 Развод")
async def m_divorce(msg: Message):
    clear_state(msg.from_user.id)
    u = await get_user(msg.from_user.id)
    ps = await partners_of(u)
    if not ps:
        await say(msg, "❌ Вы не в браке.", marry_menu()); return
    if len(ps) == 1:
        await do_divorce(msg, ps[0][1]); return
    names = {}
    for _, pid in ps:
        names[f"💔 {dn(await get_user(pid))}"] = pid
    set_state(msg.from_user.id, "divorce_pick", names=names)
    await say(msg, "С кем разводимся?", K(*[[n] for n in names], [BACK]))


@action("divorce_pick")
async def act_divorce_pick(msg: Message, st):
    pid = st["names"].get(msg.text)
    if not pid:
        await say(msg, "Выберите партнёра кнопкой 👇"); return
    await do_divorce(msg, pid)


# ==================== РП ДЕЙСТВИЯ ====================
@dp.message(F.text == "🎭 РП Действия")
async def m_rp(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, "🎭 Выберите действие, потом укажите кого 👇", rp_menu())


async def do_rp(msg: Message, key: str, target_id: int):
    uid = msg.from_user.id
    clear_state(uid)
    if target_id == uid:
        await say(msg, "❌ С собой нельзя!", rp_menu()); return
    emoji, verb, variants = RP_ACTIONS[key]
    me, target = await get_user(uid), await get_user(target_id)
    text = f"{emoji} {dn(me)} {verb} {dn(target)} {random.choice(variants)}"
    await say(msg, text, rp_menu())
    if msg.chat.type == "private":
        await notify(target_id, text)


@dp.message(F.text.in_(set(RP_ACTIONS)))
async def m_rp_action(msg: Message):
    if msg.reply_to_message and msg.reply_to_message.from_user:
        await do_rp(msg, msg.text, msg.reply_to_message.from_user.id)
        return
    set_state(msg.from_user.id, "rp_target", rp=msg.text)
    await say(msg, "Кого? Отправьте @username или ник игрока.", K([CANCEL]))


@action("rp_target")
async def act_rp_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Попробуйте ещё раз:", K([CANCEL])); return
    await do_rp(msg, st["rp"], target["user_id"])


# ==================== МОДЕРАЦИЯ (в группах, ответом на сообщение) ====================
async def check_mod(msg: Message, perm: str) -> bool:
    if msg.chat.type == "private":
        await msg.answer("❌ Только в группах")
        return False
    if not await has_perm(msg.from_user.id, msg.chat.id, perm):
        await msg.answer(f"❌ Нет прав на {perm}")
        return False
    return True

@dp.message(Command("ban"))
async def ban_cmd(msg: Message):
    if not await check_mod(msg, "ban"): return
    if not msg.reply_to_message: return
    user_id = msg.reply_to_message.from_user.id
    target = msg.reply_to_message.from_user.full_name
    try:
        await bot.ban_chat_member(msg.chat.id, user_id)
        await msg.answer(f"🔨 {target} забанен")
    except Exception as e:
        await msg.answer(f"❌ {e}")

@dp.message(Command("kick"))
async def kick_cmd(msg: Message):
    if not await check_mod(msg, "kick"): return
    if not msg.reply_to_message: return
    user_id = msg.reply_to_message.from_user.id
    target = msg.reply_to_message.from_user.full_name
    try:
        await bot.ban_chat_member(msg.chat.id, user_id)
        await bot.unban_chat_member(msg.chat.id, user_id)
        await msg.answer(f"👢 {target} кикнут")
    except Exception as e:
        await msg.answer(f"❌ {e}")

@dp.message(Command("mute"))
async def mute_cmd(msg: Message):
    if not await check_mod(msg, "mute"): return
    if not msg.reply_to_message: return
    user_id = msg.reply_to_message.from_user.id
    target = msg.reply_to_message.from_user.full_name
    duration = 60
    parts = msg.text.split()
    if len(parts) > 1:
        try: duration = int(parts[1])
        except: pass
    until = datetime.now() + timedelta(minutes=duration)
    try:
        await bot.restrict_chat_member(msg.chat.id, user_id, ChatPermissions(can_send_messages=False), until_date=until)
        await msg.answer(f"🔇 {target} замьючен на {duration} мин")
    except Exception as e:
        await msg.answer(f"❌ {e}")

@dp.message(Command("warn"))
async def warn_cmd(msg: Message):
    if not await check_mod(msg, "warn"): return
    if not msg.reply_to_message: return
    user_id = msg.reply_to_message.from_user.id
    target = msg.reply_to_message.from_user.full_name
    reason = " ".join(msg.text.split()[1:]) or "Без причины"
    await db.execute("INSERT INTO warns (chat_id, user_id, reason, date, warned_by) VALUES (?, ?, ?, ?, ?)", (msg.chat.id, user_id, reason, datetime.now().isoformat(), msg.from_user.id))
    await db.execute("UPDATE users SET warns = warns + 1 WHERE user_id = ?", (user_id,))
    await db.commit()
    async with db.execute("SELECT warns FROM users WHERE user_id = ?", (user_id,)) as cursor:
        count = (await cursor.fetchone())[0]
    await msg.answer(f"⚠️ {target} получил варн [{count}/3]\n📝 {reason}")

@dp.message(Command("clear"))
async def clear_cmd(msg: Message):
    if not await check_mod(msg, "warn"): return
    args = msg.text.split()
    if len(args) < 2: return
    try: count = min(int(args[1]), 100)
    except: return
    try:
        messages = []
        async for m in bot.get_chat_history(msg.chat.id, limit=count + 1):
            messages.append(m.message_id)
        await bot.delete_messages(msg.chat.id, messages)
        await msg.answer(f"✅ Удалено {count} сообщений")
    except: pass



# ==================== КЛАНЫ ====================
def clan_cap(level: int) -> int:
    return 10 + 5 * (level - 1)


def clan_members(clan) -> list:
    try:
        return json.loads(clan["members"]) if clan["members"] else []
    except Exception:
        return []


async def clan_of(uid: int):
    u = await get_user(uid)
    if not u["clan_id"]:
        return None
    async with db.execute("SELECT * FROM clans WHERE id = ?", (u["clan_id"],)) as c:
        return await c.fetchone()


@dp.message(F.text == "🏰 Кланы")
async def m_clans(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, f"🏰 КЛАНЫ\nСоздание клана — {fmt(CLAN_CREATE_COST)} ❄️.\nВступайте, вкладывайте в казну и улучшайте клан вместе 👇", clan_menu())


@dp.message(F.text == "🏰 Мой клан")
async def m_my_clan(msg: Message):
    clear_state(msg.from_user.id)
    clan = await clan_of(msg.from_user.id)
    if not clan:
        await say(msg, "❌ Вы не в клане. Создайте свой или вступите по тегу.", clan_menu()); return
    owner = await get_user(clan["owner_id"])
    members = clan_members(clan)
    await say(msg, f"🏰 {clan['name']} [{clan['tag']}]\n👑 Глава: {dn(owner)}\n📊 Уровень: {clan['level']}\n"
                   f"👥 Участников: {len(members)}/{clan_cap(clan['level'])}\n💰 Казна: {fmt(clan['balance'])} ❄️", clan_menu())


@dp.message(F.text == "🏰 Создать клан")
async def m_clan_create(msg: Message):
    u = await get_user(msg.from_user.id)
    if u["clan_id"]:
        await say(msg, "❌ Вы уже состоите в клане.", clan_menu()); return
    if u["balance"] < CLAN_CREATE_COST:
        await say(msg, f"❌ Нужно {fmt(CLAN_CREATE_COST)} ❄️, у вас {fmt(u['balance'])}.", clan_menu()); return
    set_state(msg.from_user.id, "clan_name")
    await say(msg, "🏰 Придумайте название клана (3–20 символов):", K([CANCEL]))


@action("clan_name")
async def act_clan_name(msg: Message, st):
    name = (msg.text or "").strip()
    if not 3 <= len(name) <= 20:
        await say(msg, "❌ Название должно быть от 3 до 20 символов."); return
    async with db.execute("SELECT id FROM clans WHERE lower(name) = lower(?)", (name,)) as c:
        if await c.fetchone():
            await say(msg, "❌ Такое название уже занято. Придумайте другое:"); return
    set_state(msg.from_user.id, "clan_tag", name=name)
    await say(msg, f"Название: {name}\nТеперь тег клана (2–5 букв или цифр, например FAMQ):", K([CANCEL]))


@action("clan_tag")
async def act_clan_tag(msg: Message, st):
    uid = msg.from_user.id
    tag = (msg.text or "").strip().upper()
    if not 2 <= len(tag) <= 5 or not tag.isalnum():
        await say(msg, "❌ Тег — от 2 до 5 букв или цифр без пробелов."); return
    async with db.execute("SELECT id FROM clans WHERE upper(tag) = ?", (tag,)) as c:
        if await c.fetchone():
            await say(msg, "❌ Такой тег уже занят. Придумайте другой:"); return
    if not await spend(uid, CLAN_CREATE_COST):
        clear_state(uid)
        await say(msg, f"❌ Нужно {fmt(CLAN_CREATE_COST)} ❄️.", clan_menu()); return
    try:
        cur = await db.execute("INSERT INTO clans (name, tag, owner_id, members, created) VALUES (?, ?, ?, ?, ?)",
                               (st["name"], tag, uid, json.dumps([uid]), datetime.now().isoformat()))
        await db.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (cur.lastrowid, uid))
        await db.commit()
    except Exception:
        await give(uid, CLAN_CREATE_COST)
        clear_state(uid)
        await say(msg, "❌ Не удалось создать клан. Деньги возвращены.", clan_menu()); return
    clear_state(uid)
    await say(msg, f"✅ Клан {st['name']} [{tag}] создан!", clan_menu())


@dp.message(F.text == "🚪 Вступить")
async def m_clan_join(msg: Message):
    u = await get_user(msg.from_user.id)
    if u["clan_id"]:
        await say(msg, "❌ Вы уже состоите в клане.", clan_menu()); return
    set_state(msg.from_user.id, "clan_join")
    await say(msg, "🚪 Введите тег клана, в который хотите вступить:", K([CANCEL]))


@action("clan_join")
async def act_clan_join(msg: Message, st):
    uid = msg.from_user.id
    tag = (msg.text or "").strip().upper()
    async with db.execute("SELECT * FROM clans WHERE upper(tag) = ?", (tag,)) as c:
        clan = await c.fetchone()
    if not clan:
        await say(msg, "❌ Клан с таким тегом не найден. Попробуйте ещё раз:", K([CANCEL])); return
    members = clan_members(clan)
    if len(members) >= clan_cap(clan["level"]):
        clear_state(uid)
        await say(msg, "❌ В клане нет свободных мест.", clan_menu()); return
    members.append(uid)
    await db.execute("UPDATE clans SET members = ? WHERE id = ?", (json.dumps(members), clan["id"]))
    await db.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan["id"], uid))
    await db.commit()
    clear_state(uid)
    await say(msg, f"✅ Вы вступили в клан {clan['name']} [{clan['tag']}]!", clan_menu())
    await notify(clan["owner_id"], f"🏰 В ваш клан вступил(а) {msg.from_user.full_name}!")


@dp.message(F.text == "💰 Казна")
async def m_clan_treasury(msg: Message):
    clear_state(msg.from_user.id)
    clan = await clan_of(msg.from_user.id)
    if not clan:
        await say(msg, "❌ Вы не в клане.", clan_menu()); return
    set_state(msg.from_user.id, "clan_deposit")
    await say(msg, f"💰 Казна клана: {fmt(clan['balance'])} ❄️\n{await balance_line(msg.from_user.id)}\n\nСколько вложить?", bet_kb())


@action("clan_deposit")
async def act_clan_deposit(msg: Message, st):
    uid = msg.from_user.id
    clan = await clan_of(uid)
    if not clan:
        clear_state(uid)
        await say(msg, "❌ Вы не в клане.", clan_menu()); return
    amount = parse_bet(msg.text, (await get_user(uid))["balance"])
    if amount is None or amount < 1:
        await say(msg, "❌ Введите число или выберите кнопку."); return
    if not await spend(uid, amount):
        await say(msg, "❌ Недостаточно средств."); return
    await db.execute("UPDATE clans SET balance = balance + ? WHERE id = ?", (amount, clan["id"]))
    await db.commit()
    clear_state(uid)
    await say(msg, f"✅ Вложено {fmt(amount)} ❄️. Казна: {fmt(clan['balance'] + amount)} ❄️", clan_menu())


@dp.message(F.text == "👥 Участники")
async def m_clan_members(msg: Message):
    clear_state(msg.from_user.id)
    clan = await clan_of(msg.from_user.id)
    if not clan:
        await say(msg, "❌ Вы не в клане.", clan_menu()); return
    lines = [f"👥 Участники {clan['name']} [{clan['tag']}]", ""]
    for pid in clan_members(clan):
        p = await get_user(pid)
        lines.append(("👑 " if pid == clan["owner_id"] else "• ") + dn(p))
    await say(msg, "\n".join(lines), clan_menu())


@dp.message(F.text == "📊 Топ кланов")
async def m_clan_top(msg: Message):
    clear_state(msg.from_user.id)
    async with db.execute("SELECT name, tag, balance, level FROM clans ORDER BY balance DESC LIMIT 10") as c:
        rows = await c.fetchall()
    if not rows:
        await say(msg, "📊 Кланов пока нет — создайте первый!", clan_menu()); return
    lines = ["📊 ТОП КЛАНОВ", ""]
    for i, r in enumerate(rows, 1):
        lines.append(f"{i}. {r['name']} [{r['tag']}] — ур. {r['level']}, 💰 {fmt(r['balance'])} ❄️")
    await say(msg, "\n".join(lines), clan_menu())


@dp.message(F.text == "⬆️ Улучшить клан")
async def m_clan_upgrade(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    clan = await clan_of(uid)
    if not clan:
        await say(msg, "❌ Вы не в клане.", clan_menu()); return
    if clan["owner_id"] != uid:
        await say(msg, "❌ Улучшать клан может только глава.", clan_menu()); return
    cost = 5000 * clan["level"]
    cur = await db.execute("UPDATE clans SET balance = balance - ?, level = level + 1 WHERE id = ? AND balance >= ?", (cost, clan["id"], cost))
    await db.commit()
    if cur.rowcount != 1:
        await say(msg, f"❌ Для улучшения нужно {fmt(cost)} ❄️ в казне (сейчас {fmt(clan['balance'])}).", clan_menu()); return
    await say(msg, f"⬆️ Клан улучшен до уровня {clan['level'] + 1}!\nМест для участников: {clan_cap(clan['level'] + 1)}", clan_menu())


@dp.message(F.text == "🚶 Покинуть клан")
async def m_clan_leave(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    clan = await clan_of(uid)
    if not clan:
        await say(msg, "❌ Вы не в клане.", clan_menu()); return
    members = clan_members(clan)
    if clan["owner_id"] == uid:
        if len(members) > 1:
            await say(msg, "❌ Глава не может уйти, пока в клане есть другие участники.", clan_menu()); return
        await db.execute("DELETE FROM clans WHERE id = ?", (clan["id"],))
        await db.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (uid,))
        await db.commit()
        await say(msg, "🏰 Клан распущен.", clan_menu()); return
    if uid in members:
        members.remove(uid)
    await db.execute("UPDATE clans SET members = ? WHERE id = ?", (json.dumps(members), clan["id"]))
    await db.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (uid,))
    await db.commit()
    await say(msg, "✅ Вы покинули клан.", clan_menu())


# ==================== ПИТОМЦЫ ====================
@dp.message(F.text == "🐾 Питомцы")
async def m_pets(msg: Message):
    clear_state(msg.from_user.id)
    pet = await get_pet(msg.from_user.id)
    hint = f"У вас: {pet['type']} «{pet['name']}»" if pet else "У вас пока нет питомца — загляните в «🛒 Купить питомца»"
    await say(msg, f"🐾 ПИТОМЦЫ\n{hint}", pet_menu())


async def pet_xp(uid: int, pet, n: int):
    xp = pet["xp"] + n
    await db.execute("UPDATE pets SET xp = ?, level = ? WHERE owner_id = ?", (xp, 1 + xp // 100, uid))


async def need_pet(msg: Message):
    pet = await get_pet(msg.from_user.id)
    if not pet:
        await say(msg, "❌ У вас нет питомца. Купите его в «🛒 Купить питомца».", pet_menu())
    return pet


@dp.message(F.text == "🐾 Мой питомец")
async def m_pet_stats(msg: Message):
    clear_state(msg.from_user.id)
    pet = await need_pet(msg)
    if not pet:
        return
    await say(msg, f"🐾 {pet['name']} ({pet['type']})\n📊 Ур. {pet['level']}  XP {pet['xp'] % 100}/100\n"
                   f"🍖 Сытость:  {bar(pet['hunger'])} {pet['hunger']}/100\n"
                   f"🎮 Счастье:  {bar(pet['happiness'])} {pet['happiness']}/100\n"
                   f"⚡ Энергия:  {bar(pet['energy'])} {pet['energy']}/100", pet_menu())


@dp.message(F.text == "🛒 Купить питомца")
async def m_pet_buy(msg: Message):
    if await get_pet(msg.from_user.id):
        await say(msg, "❌ У вас уже есть питомец.", pet_menu()); return
    await show_cat(msg, "pet")


@dp.message(F.text == "🍖 Покормить")
async def m_pet_feed(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    pet = await need_pet(msg)
    if not pet:
        return
    if pet["hunger"] >= 100:
        await say(msg, f"🍖 {pet['name']} и так сыт!", pet_menu()); return
    if await inv_take(uid, "pet_food"):
        gain, how = 60, "премиум-кормом"
    elif await spend(uid, 20):
        gain, how = 30, "обычным кормом (−20 ❄️)"
    else:
        await say(msg, "❌ Нужно 20 ❄️ на корм.", pet_menu()); return
    new = min(100, pet["hunger"] + gain)
    await db.execute("UPDATE pets SET hunger = ? WHERE owner_id = ?", (new, uid))
    await pet_xp(uid, pet, 10)
    await db.commit()
    await say(msg, f"🍖 {pet['name']} накормлен {how}!\nСытость: {new}/100", pet_menu())


@dp.message(F.text == "🎮 Играть")
async def m_pet_play(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    pet = await need_pet(msg)
    if not pet:
        return
    if pet["energy"] < 10:
        await say(msg, f"😴 {pet['name']} слишком устал. Уложите спать!", pet_menu()); return
    happy, energy = min(100, pet["happiness"] + 20), pet["energy"] - 10
    await db.execute("UPDATE pets SET happiness = ?, energy = ? WHERE owner_id = ?", (happy, energy, uid))
    await pet_xp(uid, pet, 15)
    await db.commit()
    await say(msg, f"🎮 Вы поиграли с {pet['name']}!\nСчастье: {happy}/100  Энергия: {energy}/100", pet_menu())


@dp.message(F.text == "😴 Уложить спать")
async def m_pet_sleep(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    pet = await need_pet(msg)
    if not pet:
        return
    if pet["energy"] >= 100:
        await say(msg, f"⚡ {pet['name']} полон сил!", pet_menu()); return
    await db.execute("UPDATE pets SET energy = 100, hunger = ? WHERE owner_id = ?", (max(0, pet["hunger"] - 10), uid))
    await db.commit()
    await say(msg, f"😴 {pet['name']} выспался! Энергия: 100/100 (сытость −10)", pet_menu())


@dp.message(F.text == "💰 Доход питомца")
async def m_pet_income(msg: Message):
    clear_state(msg.from_user.id)
    uid = msg.from_user.id
    pet = await need_pet(msg)
    if not pet:
        return
    until = await effect_until(uid, "pet_income")
    if until:
        await say(msg, f"⏳ Питомец принесёт монетки через {left_str((until - datetime.now()).total_seconds())}", pet_menu()); return
    if pet["hunger"] < 20:
        await say(msg, f"🍖 {pet['name']} голоден — сначала покормите!", pet_menu()); return
    mult = {"🐉 Дракончик": 2.0, "🦊 Лиса": 1.2, "🐶 Собака": 1.1}.get(pet["type"], 1.0)
    amount = int((20 + pet["level"] * 10 + pet["happiness"] // 5) * mult)
    await give(uid, amount)
    await effect_add(uid, "pet_income", 4)
    await say(msg, f"💰 {pet['name']} принёс вам {fmt(amount)} ❄️!\nСледующий раз через 4 часа.", pet_menu())


@dp.message(F.text == "📛 Назвать")
async def m_pet_name(msg: Message):
    pet = await need_pet(msg)
    if not pet:
        return
    set_state(msg.from_user.id, "pet_name")
    await say(msg, "📛 Как назовём питомца? (до 20 символов)", K([CANCEL]))


@action("pet_name")
async def act_pet_name(msg: Message, st):
    name = (msg.text or "").strip()
    if not 1 <= len(name) <= 20:
        await say(msg, "❌ От 1 до 20 символов."); return
    await db.execute("UPDATE pets SET name = ? WHERE owner_id = ?", (name, msg.from_user.id))
    await db.commit()
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Питомца теперь зовут {name}!", pet_menu())


# ==================== ПОДДЕРЖКА ====================
@dp.message(F.text == "🎫 Поддержка")
async def m_support(msg: Message):
    clear_state(msg.from_user.id)
    await say(msg, "🎫 ПОДДЕРЖКА\nОпишите проблему — администраторы получат ваш тикет и ответят в личных сообщениях.", support_menu())


async def create_ticket(msg: Message, question: str):
    cur = await db.execute("INSERT INTO tickets (user_id, username, question, created) VALUES (?, ?, ?, ?)",
                           (msg.from_user.id, msg.from_user.full_name, question, datetime.now().isoformat()))
    await db.commit()
    for admin_id in list(ADMIN_ID_CACHE):
        await notify(admin_id, f"🎫 Новый тикет #{cur.lastrowid} от {msg.from_user.full_name}:\n{question[:300]}")
    await say(msg, f"✅ Тикет #{cur.lastrowid} создан! Ответ придёт сюда.", support_menu())


@dp.message(F.text == "✍️ Создать тикет")
async def m_ticket_new(msg: Message):
    set_state(msg.from_user.id, "ticket_text")
    await say(msg, "✍️ Опишите ваш вопрос одним сообщением:", K([CANCEL]))


@action("ticket_text")
async def act_ticket_text(msg: Message, st):
    clear_state(msg.from_user.id)
    await create_ticket(msg, msg.text.strip()[:500])


@dp.message(Command("support"))
async def support_cmd(msg: Message):
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await m_ticket_new(msg)
        return
    await create_ticket(msg, args[1][:500])


@dp.message(F.text == "📋 Мои тикеты")
async def m_my_tickets(msg: Message):
    clear_state(msg.from_user.id)
    async with db.execute("SELECT id, status, question FROM tickets WHERE user_id = ? ORDER BY id DESC LIMIT 5", (msg.from_user.id,)) as c:
        rows = await c.fetchall()
    if not rows:
        await say(msg, "📋 У вас нет тикетов.", support_menu()); return
    lines = ["📋 ВАШИ ТИКЕТЫ", ""]
    for r in rows:
        lines.append(f"#{r['id']} {'🟢 открыт' if r['status'] == 'open' else '✅ закрыт'}: {r['question'][:50]}")
    await say(msg, "\n".join(lines), support_menu())


# ==================== АДМИН-ПАНЕЛЬ ====================
async def admin_only(msg: Message) -> bool:
    clear_state(msg.from_user.id)
    if is_global_admin(msg.from_user):
        return True
    await say(msg, "❌ Нет доступа.", main_menu())
    return False


@dp.message(F.text.in_({"⚙️ Админ-панель", BACK_ADMIN}))
async def m_admin(msg: Message):
    clear_state(msg.from_user.id)
    chat_id = msg.chat.id if msg.chat.type != "private" else 0
    if is_global_admin(msg.from_user) or await has_perm(msg.from_user.id, chat_id, "ban"):
        await say(msg, "🔐 АДМИН-ПАНЕЛЬ", admin_menu())
    else:
        await say(msg, "❌ Нет доступа.", main_menu())


@dp.message(F.text == "📊 Статистика")
async def m_stats(msg: Message):
    if not await admin_only(msg):
        return
    async def one(sql, *args):
        async with db.execute(sql, args) as c:
            return (await c.fetchone())[0] or 0
    users = await one("SELECT COUNT(*) FROM users")
    total = await one("SELECT SUM(balance) FROM users")
    banks = await one("SELECT SUM(balance) FROM bank")
    clans = await one("SELECT COUNT(*) FROM clans")
    pets = await one("SELECT COUNT(*) FROM pets")
    vips = await one("SELECT COUNT(*) FROM effects WHERE key = 'vip' AND until > ?", datetime.now().isoformat())
    tickets = await one("SELECT COUNT(*) FROM tickets WHERE status = 'open'")
    await say(msg, f"📊 СТАТИСТИКА\n👥 Игроков: {fmt(users)}\n💰 В кошельках: {fmt(total)} ❄️\n🏦 В банках: {fmt(banks)} ❄️\n"
                   f"🏰 Кланов: {clans}\n🐾 Питомцев: {pets}\n💎 Активных VIP: {vips}\n🎫 Открытых тикетов: {tickets}", admin_menu())


@dp.message(F.text == "📋 Логи")
async def m_logs(msg: Message):
    if not await admin_only(msg):
        return
    async with db.execute("SELECT admin_id, action, target, date FROM logs ORDER BY id DESC LIMIT 10") as c:
        rows = await c.fetchall()
    if not rows:
        await say(msg, "📋 Логи пусты.", admin_menu()); return
    lines = ["📋 ПОСЛЕДНИЕ ДЕЙСТВИЯ", ""]
    for r in rows:
        lines.append(f"👤 {r['admin_id']} — {r['action']} — {r['target']}\n🕐 {(r['date'] or '')[:16]}")
    await say(msg, "\n".join(lines), admin_menu())


# ----- тикеты -----
@dp.message(F.text == "🎫 Тикеты")
async def m_admin_tickets(msg: Message):
    if not await admin_only(msg):
        return
    async with db.execute("SELECT id, username, question FROM tickets WHERE status = 'open' ORDER BY id LIMIT 10") as c:
        rows = await c.fetchall()
    text = "🎫 Открытых тикетов нет." if not rows else "🎫 ОТКРЫТЫЕ ТИКЕТЫ\n\n" + "\n\n".join(
        f"#{r['id']} — {r['username']}\n📝 {r['question'][:80]}" for r in rows)
    await say(msg, text, tickets_menu())


@dp.message(F.text == "💬 Ответить на тикет")
async def m_ticket_reply(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "ticket_reply")
    await say(msg, "💬 Напишите номер тикета и ответ.\nПример: 12 Проблема решена, спасибо!", K([CANCEL]))


@action("ticket_reply")
async def act_ticket_reply(msg: Message, st):
    parts = (msg.text or "").split(maxsplit=1)
    tid = to_int(parts[0].lstrip("#")) if parts else None
    if tid is None or len(parts) < 2:
        await say(msg, "❌ Формат: номер и текст ответа. Пример: 12 Готово!"); return
    async with db.execute("SELECT user_id FROM tickets WHERE id = ?", (tid,)) as c:
        row = await c.fetchone()
    if not row:
        await say(msg, "❌ Тикет с таким номером не найден."); return
    sent = await notify(row["user_id"], f"💬 Ответ поддержки по тикету #{tid}:\n{parts[1]}")
    await db.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (tid,))
    await db.commit()
    await log_action(msg.from_user.id, "ticket_reply", f"#{tid}")
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Ответ отправлен, тикет #{tid} закрыт." if sent else f"⚠️ Тикет #{tid} закрыт, но игроку написать не удалось.", tickets_menu())


@dp.message(F.text == "✅ Закрыть тикет")
async def m_ticket_close(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "ticket_close")
    await say(msg, "Введите номер тикета, который нужно закрыть:", K([CANCEL]))


@action("ticket_close")
async def act_ticket_close(msg: Message, st):
    tid = to_int((msg.text or "").lstrip("#"))
    if tid is None:
        await say(msg, "❌ Введите номер тикета."); return
    await db.execute("UPDATE tickets SET status = 'closed' WHERE id = ?", (tid,))
    await db.commit()
    await log_action(msg.from_user.id, "ticket_close", f"#{tid}")
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Тикет #{tid} закрыт.", tickets_menu())


# ----- выдать валюту -----
@dp.message(F.text == "💰 Выдать")
async def m_admin_give(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "give_target")
    await say(msg, "💰 Кому выдать? Отправьте @username, ID или ник.", K([CANCEL]))


@action("give_target")
async def act_give_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Попробуйте ещё раз:", K([CANCEL])); return
    set_state(msg.from_user.id, "give_amount", target=target["user_id"])
    await say(msg, f"Игрок: {dn(target)}\nСколько ❄️ выдать? (отрицательное число — забрать)", K([CANCEL]))


@action("give_amount")
async def act_give_amount(msg: Message, st):
    amount = to_int(msg.text)
    if amount is None or amount == 0:
        await say(msg, "❌ Введите число."); return
    target = await get_user(st["target"])
    await db.execute("UPDATE users SET balance = MAX(0, balance + ?) WHERE user_id = ?", (amount, st["target"]))
    await db.commit()
    await log_action(msg.from_user.id, "give", f"{st['target']}: {amount}")
    clear_state(msg.from_user.id)
    await say(msg, f"✅ {dn(target)}: {'+' if amount > 0 else ''}{fmt(amount)} ❄️", admin_menu())
    if amount > 0:
        await notify(st["target"], f"🎁 Администратор выдал вам {fmt(amount)} ❄️!")


# ----- рассылка -----
@dp.message(F.text == "📢 Рассылка")
async def m_broadcast(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "broadcast_text")
    await say(msg, "📢 Напишите текст рассылки:", K([CANCEL]))


@action("broadcast_text")
async def act_broadcast_text(msg: Message, st):
    set_state(msg.from_user.id, "broadcast_confirm", text=msg.text)
    await say(msg, f"📢 Отправить всем игрокам?\n\n{msg.text}", K(["✅ Отправить всем"], [CANCEL]))


@action("broadcast_confirm")
async def act_broadcast_confirm(msg: Message, st):
    if msg.text != "✅ Отправить всем":
        await say(msg, "Нажмите «✅ Отправить всем» или «❌ Отмена»."); return
    if not is_global_admin(msg.from_user):
        clear_state(msg.from_user.id)
        return
    async with db.execute("SELECT user_id FROM users") as c:
        users = await c.fetchall()
    ok = 0
    await say(msg, f"⏳ Отправляю {len(users)} игрокам…")
    for r in users:
        if await notify(r["user_id"], f"📢 РАССЫЛКА\n\n{st['text']}"):
            ok += 1
        await asyncio.sleep(0.05)
    await log_action(msg.from_user.id, "broadcast", f"{ok}/{len(users)}")
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Доставлено: {ok} из {len(users)}", admin_menu())


# ----- промокоды -----
@dp.message(F.text == "🎁 Промо-коды")
async def m_admin_promo(msg: Message):
    if not await admin_only(msg):
        return
    await say(msg, "🎁 ПРОМОКОДЫ", promo_menu())


@dp.message(F.text == "➕ Создать промокод")
async def m_promo_create(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "promo_create")
    await say(msg, "Введите: КОД СУММА ИСПОЛЬЗОВАНИЙ\nПример: SUMMER 500 10", K([CANCEL]))


@action("promo_create")
async def act_promo_create(msg: Message, st):
    parts = (msg.text or "").split()
    reward = to_int(parts[1]) if len(parts) > 1 else None
    uses = to_int(parts[2]) if len(parts) > 2 else 1
    if len(parts) < 2 or reward is None or reward <= 0 or uses is None or uses <= 0:
        await say(msg, "❌ Формат: КОД СУММА ИСПОЛЬЗОВАНИЙ. Пример: SUMMER 500 10"); return
    code = parts[0].upper()
    await db.execute("INSERT OR REPLACE INTO promocodes (code, reward, uses, used_by, created_by) VALUES (?, ?, ?, '[]', ?)",
                     (code, reward, uses, msg.from_user.id))
    await db.commit()
    await log_action(msg.from_user.id, "promo_create", f"{code} {reward}x{uses}")
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Промокод {code}: {fmt(reward)} ❄️, активаций: {uses}", promo_menu())


@dp.message(F.text == "📋 Список промокодов")
async def m_promo_list(msg: Message):
    if not await admin_only(msg):
        return
    async with db.execute("SELECT code, reward, uses FROM promocodes") as c:
        rows = await c.fetchall()
    text = "📋 Промокодов нет." if not rows else "🎁 ПРОМОКОДЫ\n" + "\n".join(f"{r['code']} — {fmt(r['reward'])} ❄️ (осталось {r['uses']})" for r in rows)
    await say(msg, text, promo_menu())


@dp.message(F.text == "🗑 Удалить промокод")
async def m_promo_delete(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "promo_delete")
    await say(msg, "Введите код промокода для удаления:", K([CANCEL]))


@action("promo_delete")
async def act_promo_delete(msg: Message, st):
    code = (msg.text or "").strip().upper()
    await db.execute("DELETE FROM promocodes WHERE code = ?", (code,))
    await db.commit()
    await log_action(msg.from_user.id, "promo_delete", code)
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Промокод {code} удалён.", promo_menu())


# ----- глобальный бан -----
@dp.message(F.text == "🔨 Глобальный бан")
async def m_gban(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "gban")
    await say(msg, "🔨 Введите игрока и причину.\nПример: @username спам", K([CANCEL]))


@action("gban")
async def act_gban(msg: Message, st):
    parts = (msg.text or "").split(maxsplit=1)
    target = await find_user(parts[0]) if parts else None
    if not target:
        await say(msg, "❌ Игрок не найден. Формат: @username причина", K([CANCEL])); return
    if target["user_id"] in ADMIN_ID_CACHE:
        await say(msg, "❌ Нельзя забанить администратора.", K([CANCEL])); return
    reason = parts[1] if len(parts) > 1 else "Без причины"
    await db.execute("INSERT OR REPLACE INTO gbans (user_id, reason, date, banned_by) VALUES (?, ?, ?, ?)",
                     (target["user_id"], reason, datetime.now().isoformat(), msg.from_user.id))
    await db.commit()
    await log_action(msg.from_user.id, "gban", str(target["user_id"]), 0, reason)
    clear_state(msg.from_user.id)
    await say(msg, f"🌍 {dn(target)} забанен глобально.\n📝 {reason}", admin_menu())


@dp.message(F.text == "🕊 Разбан")
async def m_ungban(msg: Message):
    if not await admin_only(msg):
        return
    set_state(msg.from_user.id, "ungban")
    await say(msg, "🕊 Введите @username, ID или ник игрока для разбана:", K([CANCEL]))


@action("ungban")
async def act_ungban(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден.", K([CANCEL])); return
    await db.execute("DELETE FROM gbans WHERE user_id = ?", (target["user_id"],))
    await db.commit()
    await log_action(msg.from_user.id, "ungban", str(target["user_id"]))
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Глобальный бан с {dn(target)} снят.", admin_menu())


# ----- ранги в чате -----
@dp.message(F.text == "🏆 Назначить ранг")
async def m_setrank(msg: Message):
    clear_state(msg.from_user.id)
    if msg.chat.type == "private":
        await say(msg, "❌ Ранги назначаются в группе: откройте админ-панель там.", admin_menu()); return
    if not await has_perm(msg.from_user.id, msg.chat.id, "setrank"):
        await say(msg, "❌ Нет прав.", admin_menu()); return
    set_state(msg.from_user.id, "rank_target", chat=msg.chat.id)
    await say(msg, "🏆 Кому назначить ранг? Отправьте @username или ник.", K([CANCEL]))


@action("rank_target")
async def act_rank_target(msg: Message, st):
    target = await find_user(msg.text)
    if not target:
        await say(msg, "❌ Игрок не найден. Попробуйте ещё раз:", K([CANCEL])); return
    options = {f"{r} · {RANKS[r]['name']}": r for r in (1, 2, 3, 4)}
    set_state(msg.from_user.id, "rank_pick", chat=st["chat"], target=target["user_id"], options=options)
    await say(msg, f"Игрок: {dn(target)}\nВыберите ранг:", K(*[[o] for o in options], [CANCEL]))


@action("rank_pick")
async def act_rank_pick(msg: Message, st):
    rank = st["options"].get(msg.text)
    if rank is None:
        await say(msg, "Выберите ранг кнопкой 👇"); return
    await db.execute("INSERT OR REPLACE INTO user_ranks (user_id, chat_id, rank) VALUES (?, ?, ?)", (st["target"], st["chat"], rank))
    await db.commit()
    await log_action(msg.from_user.id, "setrank", f"{st['target']}={rank}", st["chat"])
    clear_state(msg.from_user.id)
    await say(msg, f"✅ Новый ранг: {RANKS[rank]['name']}", admin_menu())


@dp.message(F.text == "👥 Админы чата")
async def m_chat_admins(msg: Message):
    clear_state(msg.from_user.id)
    if msg.chat.type == "private":
        await say(msg, "❌ Эта кнопка работает в группе.", admin_menu()); return
    if not await has_perm(msg.from_user.id, msg.chat.id, "ban"):
        await say(msg, "❌ Нет доступа.", admin_menu()); return
    async with db.execute("SELECT user_id, rank FROM user_ranks WHERE chat_id = ? AND rank > 1", (msg.chat.id,)) as c:
        rows = await c.fetchall()
    if not rows:
        await say(msg, "🏆 В этом чате нет назначенных рангов.", admin_menu()); return
    lines = ["👥 АДМИНИСТРАЦИЯ ЧАТА", ""]
    for r in rows:
        lines.append(f"{RANKS[r['rank']]['name']} — {dn(await get_user(r['user_id']))}")
    await say(msg, "\n".join(lines), admin_menu())


# ==================== РАЗВЛЕЧЕНИЯ ====================
@dp.message(F.text.in_({"😄 Шутка"}))
async def m_joke(msg: Message): await say(msg, f"😄 {random.choice(JOKES)}", games_menu())


@dp.message(F.text.in_({"📚 Факт"}))
async def m_fact(msg: Message): await say(msg, f"📚 {random.choice(FACTS)}", games_menu())


@dp.message(F.text.in_({"💬 Цитата"}))
async def m_quote(msg: Message): await say(msg, f"💬 {random.choice(QUOTES)}", games_menu())


@dp.message(Command("joke"))
async def joke_cmd(msg: Message): await m_joke(msg)


@dp.message(Command("fact"))
async def fact_cmd(msg: Message): await m_fact(msg)


@dp.message(Command("quote"))
async def quote_cmd(msg: Message): await m_quote(msg)


@dp.message(F.text == "🎱 Шар судьбы")
async def m_ball(msg: Message):
    set_state(msg.from_user.id, "ball")
    await say(msg, "🎱 Задайте вопрос, на который можно ответить «да» или «нет»:", K([BACK]))


@action("ball")
async def act_ball(msg: Message, st):
    await say(msg, f"🎱 {random.choice(BALL_ANSWERS)}", K([BACK]))


@dp.message(F.new_chat_members)
async def welcome_new_member(msg: Message):
    async with db.execute("SELECT welcome, welcome_text FROM chats WHERE chat_id = ?", (msg.chat.id,)) as cursor:
        result = await cursor.fetchone()
    if result and result[0] == 0:
        return
    welcome_text = result[1] if result and result[1] else None
    for member in msg.new_chat_members:
        if member.id == bot.id:
            await msg.answer(f"❄️ {BOT_NAME} активирован!\nНапишите мне в личные сообщения /start — там все кнопки.")
        else:
            await msg.answer(welcome_text if welcome_text else f"👋 Привет, {member.full_name}!")


# ==================== ЗАПУСК ====================
async def main():
    await init_db()
    print(f"✅ {BOT_NAME} v{VERSION} запущен!")
    print(f"📁 База данных: {DB_NAME}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
