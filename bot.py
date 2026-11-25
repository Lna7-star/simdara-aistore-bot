"""
Ai STORE KH - Telegram Shop Bot
=================================
Bot លក់គណនី AI ដូច ChatGPT Plus, Gemini Plus
មាន៖ ផលិតផល, ស្តុក, សមតុល្យ, ដាក់ប្រាក់, ទិញអូតូ, Admin

របៀបដំណើរការ៖
  pip install -r requirements.txt
  cp .env.example .env  (ហើយបំពេញ BOT_TOKEN, ADMIN_IDS)
  python bot.py

បង្កើតដោយ Muse សម្រាប់ Lim - 25 វិច្ឆិកា 2026
"""

import os
import sqlite3
import logging
from datetime import datetime

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "@aistorekh")
ABA_NAME = os.getenv("ABA_NAME", "SIM DARA")
ABA_ACCOUNT = os.getenv("ABA_ACCOUNT", "000 000 000")
WING_NUMBER = os.getenv("WING_NUMBER", "012 000 000")
USDT_ADDRESS = os.getenv("USDT_ADDRESS", "Txxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
DB_PATH = os.getenv("DB_PATH", "shop.db")

# Conversation states
ADDSTOCK_PRODUCT, ADDSTOCK_LINES = range(2)
TOPUP_AMOUNT = 10
ADDPRODUCT_INFO = 20

# ---------- Database ----------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            balance REAL DEFAULT 0,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            price REAL NOT NULL,
            active INTEGER DEFAULT 1
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            note TEXT DEFAULT '',
            is_sold INTEGER DEFAULT 0,
            sold_to INTEGER,
            sold_at TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            price REAL NOT NULL,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            method TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT
        )
    """)
    # Seed products ដូចក្នុងរូប Screenshot - បើ DB ទទេ
    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
            ("Chatgpt plus 1M (Google pay) Gmail NW",
             "ChatGPT Plus 1 ខែ - Gmail ថ្មី - ប្រើបានពេញលេញ",
             6.31),
        )
        cur.execute(
            "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
            ("Gemini Plus 12M (Credit Card)",
             "Gemini Plus 12 ខែ - បង់តាម Credit Card",
             1.75),
        )
        cur.execute(
            "INSERT INTO products (name, description, price) VALUES (?, ?, ?)",
            ("Chatgpt plus 12M (Google pay)",
             "ChatGPT Plus 12 ខែ - Gmail ថ្មី",
             45.00),
        )
    conn.commit()
    conn.close()


def ensure_user(user):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    row = cur.fetchone()
    if not row:
        cur.execute(
            "INSERT INTO users (user_id, username, balance, created_at) VALUES (?, ?, 0, ?)",
            (user.id, user.username or user.first_name, datetime.now().isoformat()),
        )
        conn.commit()
        row = cur.execute("SELECT * FROM users WHERE user_id=?", (user.id,)).fetchone()
    conn.close()
    return row


def get_balance(user_id):
    conn = get_db()
    row = conn.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return row["balance"] if row else 0.0


def stock_count(product_id):
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) c FROM stock WHERE product_id=? AND is_sold=0",
        (product_id,),
    ).fetchone()
    conn.close()
    return row["c"]


def is_admin(user_id):
    return user_id in ADMIN_IDS


# ---------- Keyboards ----------

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍️ ស្វែងរក Products", callback_data="products")],
        [InlineKeyboardButton("👤 My Profile", callback_data="profile"),
         InlineKeyboardButton("💰 ដាក់ប្រាក់ក្នុងគណនី", callback_data="topup")],
        [InlineKeyboardButton("🆘 Support", callback_data="support")],
    ])


def back_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ ត្រឡប់ទៅ Menu", callback_data="menu")]
    ])


# ---------- User handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user)
    text = (
        f"សួស្តី {user.first_name}! 👋\n\n"
        "សូមស្វាគមន៍មកកាន់ **Ai STORE KH** 🛒\n"
        "លក់គណនី ChatGPT Plus, Gemini Plus តម្លៃធូរៗ\n\n"
        "ជ្រើសរើសមុខម្ហូបខាងក្រោម៖"
    )
    if update.message:
        await update.message.reply_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = get_db()
    products = conn.execute("SELECT * FROM products WHERE active=1").fetchall()
    conn.close()
    if not products:
        await query.edit_message_text("មិនទាន់មានផលិតផលទេ។", reply_markup=back_menu())
        return
    buttons = []
    for p in products:
        count = stock_count(p["id"])
        buttons.append([InlineKeyboardButton(
            f"{p['name']} - ${p['price']:.2f} (ស្តុក {count})",
            callback_data=f"product_{p['id']}"
        )])
    buttons.append([InlineKeyboardButton("⬅️ ត្រឡប់ទៅ Menu", callback_data="menu")])
    await query.edit_message_text(
        "🛍️ **បញ្ជីផលិតផល**\nចុចលើផលិតផលដើម្បីមើលលម្អិត៖",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def show_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = int(query.data.split("_")[1])
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not p:
        await query.edit_message_text("រកមិនឃើញផលិតផលនេះទេ។", reply_markup=back_menu())
        return
    count = stock_count(pid)
    text = (
        f"🎉 **{p['name']}**\n\n"
        f"{p['description']}\n\n"
        f"🛒 ស្តុក៖ +{count}\n"
        f"មានក្នុងស្តុក៖ {count}\n"
        f"💵 តម្លៃ៖ **${p['price']:.2f}**\n"
        f"⚡ ទទួលបានភ្លាមៗបន្ទាប់ពីទិញ"
    )
    buttons = []
    if count > 0:
        buttons.append([InlineKeyboardButton("✅ ទិញឥឡូវនេះ", callback_data=f"buy_{pid}")])
    else:
        buttons.append([InlineKeyboardButton("❌ អស់ស្តុក", callback_data="products")])
    buttons.append([InlineKeyboardButton("⬅️ ត្រឡប់ទៅផលិតផល", callback_data="products")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")


async def buy_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    ensure_user(user)
    pid = int(query.data.split("_")[1])

    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not p:
        conn.close()
        await query.edit_message_text("រកមិនឃើញផលិតផលនេះទេ។", reply_markup=back_menu())
        return

    balance = get_balance(user.id)
    if balance < p["price"]:
        conn.close()
        await query.edit_message_text(
            f"❌ សមតុល្យរបស់អ្នកមិនគ្រប់ទេ។\n\n"
            f"តម្លៃ៖ ${p['price']:.2f}\n"
            f"សមតុល្យរបស់អ្នក៖ ${balance:.2f}\n"
            f"ខ្វះ៖ ${p['price'] - balance:.2f}\n\n"
            "សូមដាក់ប្រាក់ជាមុនសិន។",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 ដាក់ប្រាក់", callback_data="topup")],
                [InlineKeyboardButton("⬅️ ត្រឡប់", callback_data="menu")],
            ]),
        )
        return

    # យកស្តុកចាស់បំផុត 1 ដែលមិនទាន់លក់
    item = conn.execute(
        "SELECT * FROM stock WHERE product_id=? AND is_sold=0 ORDER BY id ASC LIMIT 1",
        (pid,),
    ).fetchone()
    if not item:
        conn.close()
        await query.edit_message_text("❌ ផលិតផលនេះអស់ស្តុកហើយ។ សូមរង់ចាំ Admin បន្ថែមស្តុក។", reply_markup=back_menu())
        return

    now = datetime.now().isoformat()
    cur = conn.cursor()
    cur.execute("UPDATE users SET balance = balance - ? WHERE user_id=?", (p["price"], user.id))
    cur.execute(
        "UPDATE stock SET is_sold=1, sold_to=?, sold_at=? WHERE id=?",
        (user.id, now, item["id"]),
    )
    cur.execute(
        "INSERT INTO orders (user_id, product_id, stock_id, price, created_at) VALUES (?, ?, ?, ?, ?)",
        (user.id, pid, item["id"], p["price"], now),
    )
    conn.commit()
    conn.close()

    new_balance = get_balance(user.id)
    text = (
        "✅ **ទិញជោគជ័យ!** 🎉\n\n"
        f"ផលិតផល៖ {p['name']}\n"
        f"តម្លៃ៖ ${p['price']:.2f}\n"
        f"សមតុល្យនៅសល់៖ ${new_balance:.2f}\n\n"
        "🔑 **គណនីរបស់អ្នក៖**\n"
        f"Gmail៖ `{item['email']}`\n"
        f"Password៖ `{item['password']}`\n"
    )
    if item["note"]:
        text += f"ចំណាំ៖ {item['note']}\n"
    text += (
        "\n⚠️ សូមរក្សាទុកឲ្យបានល្អ កុំចែករំលែកឲ្យអ្នកដទៃ។\n"
        "បើមានបញ្ហា សូមទាក់ទង Support។"
    )
    await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")

    # ជូនដំណឹងទៅ Admin
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🛒 លក់បាន 1!\n{user.first_name} (@{user.username}) ទិញ {p['name']} តម្លៃ ${p['price']:.2f}",
            )
        except Exception as e:
            logger.warning("Cannot notify admin %s: %s", admin_id, e)


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    ensure_user(user)
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE user_id=?", (user.id,)).fetchone()
    order_count = conn.execute("SELECT COUNT(*) c FROM orders WHERE user_id=?", (user.id,)).fetchone()["c"]
    conn.close()
    text = (
        "👤 **My Profile**\n\n"
        f"ឈ្មោះ៖ {user.first_name}\n"
        f"Username៖ @{user.username or '-'}\n"
        f"User ID៖ `{user.id}`\n"
        f"💰 សមតុល្យ៖ **${row['balance']:.2f}**\n"
        f"🛒 ទិញសរុប៖ {order_count} ដង"
    )
    await query.edit_message_text(text, reply_markup=main_menu(), parse_mode="Markdown")


async def show_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    buttons = [
        [InlineKeyboardButton("🏦 ABA KHQR", callback_data="topup_ABA")],
        [InlineKeyboardButton("💜 Wing", callback_data="topup_Wing")],
        [InlineKeyboardButton("₮ USDT TRC20", callback_data="topup_USDT")],
        [InlineKeyboardButton("⬅️ ត្រឡប់ទៅ Menu", callback_data="menu")],
    ]
    await query.edit_message_text(
        "💰 **ដាក់ប្រាក់ក្នុងគណនី**\nជ្រើសរើសវិធីបង់ប្រាក់៖",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown",
    )


async def topup_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    method = query.data.split("_")[1]
    context.user_data["topup_method"] = method
    if method == "ABA":
        info = f"🏦 **ABA KHQR**\nឈ្មោះ៖ {ABA_NAME}\nគណនី៖ {ABA_ACCOUNT}\n\nស្កេន KHQR ឬផ្ទេរតាមលេខគណនីខាងលើ។"
    elif method == "Wing":
        info = f"💜 **Wing**\nលេខ៖ {WING_NUMBER}\nឈ្មោះ៖ {ABA_NAME}"
    else:
        info = f"₮ **USDT TRC20**\nAddress៖\n`{USDT_ADDRESS}`\n\nសូមផ្ទេរតាមបណ្តាញ TRC20 តែប៉ុណ្ណោះ។"
    await query.edit_message_text(
        info + "\n\nសូមវាយចំនួនលុយដែលអ្នកចង់ដាក់ ជាលេខ ឧទាហរណ៍ `10` ឬ `6.31`",
        reply_markup=back_menu(),
        parse_mode="Markdown",
    )
    return TOPUP_AMOUNT


async def topup_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = float(update.message.text.strip().replace("$", ""))
        if amount <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("សូមវាយចំនួនលុយជាលេខ ឧទាហរណ៍ 10")
        return TOPUP_AMOUNT

    method = context.user_data.get("topup_method", "ABA")
    user = update.effective_user
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO topups (user_id, amount, method, created_at) VALUES (?, ?, ?, ?)",
        (user.id, amount, method, datetime.now().isoformat()),
    )
    topup_id = cur.lastrowid
    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"📩 បានទទួលសំណើដាក់ប្រាក់ **${amount:.2f}** តាម {method} ហើយ។\n"
        "សូមរង់ចាំ Admin អនុម័ត។ បើបង់រួចហើយ សូមផ្ញើ Screenshot មកទីនេះក៏បាន។",
        reply_markup=main_menu(),
        parse_mode="Markdown",
    )
    # ជូនដំណឹងទៅ Admin ព្រមទាំងប៊ូតុង Approve
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"💰 សំណើដាក់ប្រាក់ #{topup_id}\n"
                f"អ្នកប្រើ៖ {user.first_name} (@{user.username}) ID `{user.id}`\n"
                f"ចំនួន៖ ${amount:.2f} តាម {method}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{topup_id}"),
                     InlineKeyboardButton("❌ Reject", callback_data=f"reject_{topup_id}")]
                ]),
            )
        except Exception as e:
            logger.warning("Cannot notify admin %s: %s", admin_id, e)
    return ConversationHandler.END


async def approve_topup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.edit_message_text("អ្នកមិនមែន Admin ទេ។")
        return
    tid = int(query.data.split("_")[1])
    approve = query.data.startswith("approve_")
    conn = get_db()
    row = conn.execute("SELECT * FROM topups WHERE id=?", (tid,)).fetchone()
    if not row or row["status"] != "pending":
        conn.close()
        await query.edit_message_text("សំណើនេះត្រូវបានដោះស្រាយរួចហើយ។")
        return
    cur = conn.cursor()
    if approve:
        cur.execute("UPDATE topups SET status='approved' WHERE id=?", (tid,))
        cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (row["amount"], row["user_id"]))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"✅ បាន Approve ដាក់ប្រាក់ #{tid} ចំនួន ${row['amount']:.2f} ហើយ។")
        try:
            await context.bot.send_message(
                row["user_id"],
                f"✅ Admin បានអនុម័តដាក់ប្រាក់ **${row['amount']:.2f}** ហើយ។\nសមតុល្យថ្មីរបស់អ្នក៖ ${get_balance(row['user_id']):.2f}",
                parse_mode="Markdown",
            )
        except Exception:
            pass
    else:
        cur.execute("UPDATE topups SET status='rejected' WHERE id=?", (tid,))
        conn.commit()
        conn.close()
        await query.edit_message_text(f"❌ បាន Reject ដាក់ប្រាក់ #{tid} ហើយ។")
        try:
            await context.bot.send_message(row["user_id"], f"❌ សំណើដាក់ប្រាក់ ${row['amount']:.2f} ត្រូវបានបដិសេធ។ សូមទាក់ទង Support។")
        except Exception:
            pass


async def show_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        f"🆘 **Support**\n\nបើមានបញ្ហា សូមទាក់ទង Admin៖ {SUPPORT_USERNAME}\n"
        "ឬឆ្លើយសារនៅទីនេះ Admin នឹងឆ្លើយវិញ។",
        reply_markup=main_menu(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await start(update, context)


# ---------- Admin handlers ----------

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        await update.message.reply_text("អ្នកមិនមែន Admin ទេ។")
        return
    conn = get_db()
    total_users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    total_orders = conn.execute("SELECT COUNT(*) c FROM orders").fetchone()["c"]
    total_sales = conn.execute("SELECT COALESCE(SUM(price),0) s FROM orders").fetchone()["s"]
    pending = conn.execute("SELECT COUNT(*) c FROM topups WHERE status='pending'").fetchone()["c"]
    products = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    lines = [
        "🛠️ **Admin Panel**",
        f"👥 អ្នកប្រើសរុប៖ {total_users}",
        f"🛒 Order សរុប៖ {total_orders}",
        f"💵 លក់បានសរុប៖ ${total_sales:.2f}",
        f"⏳ Topup រង់ចាំ៖ {pending}",
        "",
        "📦 **ផលិតផល៖**",
    ]
    for p in products:
        lines.append(f"ID {p['id']} - {p['name']} - ${p['price']:.2f} - ស្តុក {stock_count(p['id'])}")
    lines += [
        "",
        "**ពាក្យបញ្ជា Admin៖**",
        "`/addproduct ឈ្មោះ | តម្លៃ | ការពិពណ៌នា`",
        "`/addstock` - បន្ថែមស្តុក (Bot នឹងសួរ ID ផលិតផល រួចសួរ Gmail:Password)",
        "`/approve <user_id> <ចំនួន>` - បន្ថែមលុយឲ្យអ្នកប្រើដោយផ្ទាល់",
        "`/pending` - មើល Topup ដែលរង់ចាំ",
    ]
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


async def add_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("អ្នកមិនមែន Admin ទេ។")
        return
    # ទម្រង់៖ /addproduct ឈ្មោះ | 6.31 | ការពិពណ៌នា
    text = update.message.text.replace("/addproduct", "", 1).strip()
    parts = [x.strip() for x in text.split("|")]
    if len(parts) < 2:
        await update.message.reply_text("ទម្រង់៖ /addproduct ឈ្មោះ | តម្លៃ | ការពិពណ៌នា\nឧទាហរណ៍៖ /addproduct ChatGPT Plus 1M | 6.31 | Gmail ថ្មី")
        return
    try:
        price = float(parts[1])
    except ValueError:
        await update.message.reply_text("តម្លៃត្រូវតែជាលេខ។")
        return
    desc = parts[2] if len(parts) > 2 else ""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", (parts[0], desc, price))
    pid = cur.lastrowid
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ បានបន្ថែមផលិតផល ID {pid}៖ {parts[0]} - ${price:.2f} ហើយ។\nបន្ថែមស្តុកដោយ /addstock")


async def addstock_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("អ្នកមិនមែន Admin ទេ។")
        return ConversationHandler.END
    await update.message.reply_text("សូមវាយ ID ផលិតផលដែលចង់បន្ថែមស្តុក។ មើល ID ដោយ /admin")
    return ADDSTOCK_PRODUCT


async def addstock_product_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        pid = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("ID ត្រូវតែជាលេខ។")
        return ADDSTOCK_PRODUCT
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    conn.close()
    if not p:
        await update.message.reply_text("រកមិនឃើញផលិតផល ID នេះទេ។")
        return ADDSTOCK_PRODUCT
    context.user_data["addstock_pid"] = pid
    await update.message.reply_text(
        f"ផលិតផល៖ {p['name']}\n\n"
        "សូមផ្ញើស្តុកជាបន្ទាត់ៗ ទម្រង់៖\n"
        "`email:password`\n"
        "មួយបន្ទាត់ = 1 គណនី\n\n"
        "ឧទាហរណ៍៖\n"
        "test1@gmail.com:pass123\n"
        "test2@gmail.com:pass456",
        parse_mode="Markdown",
    )
    return ADDSTOCK_LINES


async def addstock_lines_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pid = context.user_data.get("addstock_pid")
    lines = [l.strip() for l in update.message.text.strip().splitlines() if ":" in l]
    conn = get_db()
    cur = conn.cursor()
    added = 0
    for line in lines:
        email, password = line.split(":", 1)
        email, password = email.strip(), password.strip()
        if email and password:
            cur.execute("INSERT INTO stock (product_id, email, password) VALUES (?, ?, ?)", (pid, email, password))
            added += 1
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ បានបន្ថែមស្តុក {added} គណនីទៅផលិតផល ID {pid} ហើយ។ ស្តុកសរុបឥឡូវ៖ {stock_count(pid)}")
    return ConversationHandler.END


async def approve_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("អ្នកមិនមែន Admin ទេ។")
        return
    if len(context.args) != 2:
        await update.message.reply_text("ទម្រង់៖ /approve <user_id> <ចំនួន>\nឧទាហរណ៍៖ /approve 123456789 10")
        return
    try:
        uid = int(context.args[0])
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("user_id និងចំនួនត្រូវតែជាលេខ។")
        return
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO users (user_id, username, balance, created_at) VALUES (?, '', 0, ?)", (uid, datetime.now().isoformat()))
    cur.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, uid))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ បានបន្ថែម ${amount:.2f} ឲ្យ User {uid} ហើយ។ សមតុល្យថ្មី៖ ${get_balance(uid):.2f}")
    try:
        await context.bot.send_message(uid, f"✅ Admin បានបន្ថែមលុយ ${amount:.2f} ឲ្យអ្នកហើយ។ សមតុល្យថ្មី៖ ${get_balance(uid):.2f}")
    except Exception:
        pass


async def pending_topups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("អ្នកមិនមែន Admin ទេ។")
        return
    conn = get_db()
    rows = conn.execute("SELECT * FROM topups WHERE status='pending' ORDER BY id DESC LIMIT 20").fetchall()
    conn.close()
    if not rows:
        await update.message.reply_text("មិនមាន Topup រង់ចាំទេ។")
        return
    for r in rows:
        await update.message.reply_text(
            f"💰 Topup #{r['id']}\nUser ID៖ `{r['user_id']}`\nចំនួន៖ ${r['amount']:.2f} តាម {r['method']}\nពេល៖ {r['created_at']}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Approve", callback_data=f"approve_{r['id']}"),
                 InlineKeyboardButton("❌ Reject", callback_data=f"reject_{r['id']}")]
            ]),
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("បានបោះបង់។", reply_markup=main_menu())
    return ConversationHandler.END


# ---------- Main ----------

def main():
    if not BOT_TOKEN:
        print("❌ មិនទាន់មាន BOT_TOKEN ទេ! សូមបង្កើត .env ហើយដាក់ BOT_TOKEN=")
        print("   មើល .env.example សម្រាប់ឧទាហរណ៍")
        return
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Topup conversation - ត្រូវដាក់មុន Callback handler ទូទៅ
    topup_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(topup_method, pattern=r"^topup_(ABA|Wing|USDT)$")],
        states={TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, topup_amount_received)]},
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    addstock_conv = ConversationHandler(
        entry_points=[CommandHandler("addstock", addstock_start)],
        states={
            ADDSTOCK_PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, addstock_product_received)],
            ADDSTOCK_LINES: [MessageHandler(filters.TEXT & ~filters.COMMAND, addstock_lines_received)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("addproduct", add_product))
    app.add_handler(CommandHandler("approve", approve_direct))
    app.add_handler(CommandHandler("pending", pending_topups))
    app.add_handler(addstock_conv)
    app.add_handler(topup_conv)

    app.add_handler(CallbackQueryHandler(show_products, pattern=r"^products$"))
    app.add_handler(CallbackQueryHandler(show_product, pattern=r"^product_\d+$"))
    app.add_handler(CallbackQueryHandler(buy_product, pattern=r"^buy_\d+$"))
    app.add_handler(CallbackQueryHandler(show_profile, pattern=r"^profile$"))
    app.add_handler(CallbackQueryHandler(show_topup, pattern=r"^topup$"))
    app.add_handler(CallbackQueryHandler(show_support, pattern=r"^support$"))
    app.add_handler(CallbackQueryHandler(menu_callback, pattern=r"^menu$"))
    app.add_handler(CallbackQueryHandler(approve_topup, pattern=r"^(approve|reject)_\d+$"))

    print("✅ Bot កំពុងដំណើរការ... ចុច Ctrl+C ដើម្បីឈប់")
    app.run_polling()


if __name__ == "__main__":
    main()
