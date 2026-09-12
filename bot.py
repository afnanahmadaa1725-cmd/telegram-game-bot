# -*- coding: utf-8 -*-
"""
بوت الألعاب الاحترافي — أزرار 100%
نسخة مصححة مع:
- إبقاء فكرة وأسماء الألعاب الأصلية.
- التفعيل الاحترافي داخل الكروبات.
- التحقق من أن البوت مشرف في الكروب قبل التفعيل.
- زر "تفعيل البوت 🎮" داخل الكروب.
- زر "مناداة بوت الألعاب 🎮" لفتح قائمة الألعاب بالأزرار.
- التشغيل بالأزرار قدر الإمكان، مع إبقاء /start و /dev كاختصارات أساسية.
- إصلاح أخطاء syntax/logic في XO Tournament و Guess Multi.
"""

# =========================
# AUTO INSTALL
# =========================
def _ensure_dependencies():
    """تثبيت مكتبة البوت تلقائياً من نفس الملف."""
    import sys
    import subprocess

    try:
        import telegram  # noqa: F401
        return
    except ImportError:
        print("📦 جاري تثبيت python-telegram-bot تلقائياً...")

    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "--disable-pip-version-check",
            "python-telegram-bot>=20,<23",
        ])
    except Exception as e:
        print("❌ فشل التثبيت التلقائي:", e)
        raise SystemExit(1)

    print("✅ تم تثبيت المكتبة. جاري تشغيل البوت...")

_ensure_dependencies()

import os
import random
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatMemberStatus
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

BOT_TOKEN = "ضع_توكن_البوت_هنا"
DEV_USER = "@zz_w72"

MAX_PLAYERS = 4
GUESS_TRIES = 7
LADDER_TARGET = 10
AN_SOLO = 10
AN_MULTI_PP = 5

games = {}
enabled_chats = set()


# =========================
# عام
# =========================

DEV_LINE = f"\n\n👨‍💻 المطور: {DEV_USER}"


def back_kb():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 رجوع", callback_data="main_menu")]]
    )


def main_menu_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🎮 ألعاب البوت", callback_data="games_menu")],
            [InlineKeyboardButton("📢 مناداة بوت الألعاب", callback_data="call_games")],
            [InlineKeyboardButton("⚙️ تفعيل البوت في الكروب", callback_data="activate")],
        ]
    )


def games_kb():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("❌⭕ XO", callback_data="game:xo"),
                InlineKeyboardButton("✊📄✂️ RPS", callback_data="game:rps"),
            ],
            [
                InlineKeyboardButton("🔢 خمن الرقم", callback_data="game:guess"),
                InlineKeyboardButton("🐾 الحيوانات", callback_data="game:animal"),
            ],
            [InlineKeyboardButton("🪜 السلم", callback_data="game:ladder")],
            [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")],
        ]
    )


def xo_mode_kb():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🤖 فردي — سهل", callback_data="xo:solo:easy"),
                InlineKeyboardButton("🧠 فردي — صعب", callback_data="xo:solo:hard"),
            ],
            [InlineKeyboardButton("👥 لاعب ضد لاعب", callback_data="xo:duo")],
            [InlineKeyboardButton("🏆 بطولة 3-4 لاعبين", callback_data="xo:tournament")],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


def rps_mode_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 فردي — أول إلى 3", callback_data="rps:solo")],
            [InlineKeyboardButton("👥 جماعي 2-4", callback_data="rps:multi")],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


def guess_mode_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 فردي", callback_data="guess:solo")],
            [InlineKeyboardButton("👥 جماعي 2-4", callback_data="guess:multi")],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


def animal_mode_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 فردي — 10 أسئلة", callback_data="animal:solo")],
            [InlineKeyboardButton("👥 جماعي", callback_data="animal:multi")],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


def ladder_mode_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("🤖 فردي ضد AI", callback_data="ladder:solo")],
            [InlineKeyboardButton("👥 جماعي", callback_data="ladder:multi")],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not update.effective_chat:
        return False
    if update.effective_chat.type == "private":
        return True

    try:
        me = await context.bot.get_me()
        member = await context.bot.get_chat_member(
            update.effective_chat.id, me.id
        )
        return member.status in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except Exception:
        return False


async def require_activation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """يمنع الألعاب داخل الكروب قبل التفعيل."""
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return True

    if chat.id in enabled_chats:
        return True

    if not await is_bot_admin(update, context):
        text = (
            "⚠️ <b>لا يمكن تشغيل بوت الألعاب بعد</b>\n\n"
            "لازم ترفع البوت <b>مشرف</b> في الكروب أولاً، "
            "وبعدها اضغط زر التفعيل."
        )
        if update.callback_query:
            await update.callback_query.answer(
                "ارفع البوت مشرف أولاً.", show_alert=True
            )
            await update.callback_query.message.reply_text(
                text, parse_mode="HTML"
            )
        else:
            await update.effective_message.reply_text(
                text, parse_mode="HTML"
            )
        return False

    await activate_chat(update, context, silent=True)
    return True


async def activate_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    silent: bool = False,
):
    chat = update.effective_chat

    if not chat:
        return False

    if chat.type == "private":
        if not silent:
            await update.effective_message.reply_text(
                "🎮 التفعيل يتم تلقائياً في الخاص.\n\nاختر اللعبة من الأزرار:",
                reply_markup=games_kb(),
            )
        return True

    if not await is_bot_admin(update, context):
        text = (
            "🚫 <b>التفعيل يحتاج صلاحيات المشرف</b>\n\n"
            "1️⃣ ارفعني مشرف في الكروب.\n"
            "2️⃣ بعدها اضغط <b>تفعيل البوت 🎮</b>.\n"
            "3️⃣ بعدها يظهر لك زر <b>مناداة بوت الألعاب 🎮</b>."
        )
        if not silent:
            await update.effective_message.reply_text(
                text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔄 تحقق مرة ثانية", callback_data="activate")]]
                ),
            )
        return False

    enabled_chats.add(chat.id)

    if not silent:
        await update.effective_message.reply_text(
            "✅ <b>تم تفعيل بوت الألعاب بنجاح!</b>\n\n"
            "🎮 صار بإمكانكم مناداة البوت وعرض جميع الألعاب بالأزرار.\n"
            "📢 اضغطوا على <b>مناداة بوت الألعاب</b> لعرض قائمة الألعاب.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("📢 مناداة بوت الألعاب 🎮", callback_data="call_games")],
                    [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                ]
            ),
        )
    return True


# =========================
# /start + الواجهة الرئيسية
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat and chat.type != "private":
        admin = await is_bot_admin(update, context)
        if not admin:
            await update.effective_message.reply_text(
                "👋 <b>أهلاً بك في بوت الألعاب</b>\n\n"
                "⚠️ حتى يعمل البوت داخل الكروب يجب رفعه <b>مشرف</b>.\n\n"
                "بعد رفعه مشرف اضغط زر التفعيل:",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("⚙️ تفعيل البوت 🎮", callback_data="activate")]]
                ),
            )
            return

        await update.effective_message.reply_text(
            "🎮 <b>بوت الألعاب الاحترافي</b>\n\n"
            "البوت جاهز. اضغط مناداة بوت الألعاب حتى تظهر الألعاب.",
            parse_mode="HTML",
            reply_markup=main_menu_kb(),
        )
        return

    await update.effective_message.reply_text(
        "🎮 <b>أهلاً بك في بوت الألعاب الاحترافي</b>\n\n"
        "كل شيء من خلال الأزرار 👇",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


async def dev(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"👨‍💻 <b>المطور:</b> {DEV_USER}\n🎮 بوت الألعاب الاحترافي",
        parse_mode="HTML",
    )


async def show_main(update: Update):
    q = update.callback_query
    await q.edit_message_text(
        "🎮 <b>بوت الألعاب الاحترافي</b>\n\nاختر من الأزرار:",
        parse_mode="HTML",
        reply_markup=main_menu_kb(),
    )


async def show_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await require_activation(update, context):
        return
    q = update.callback_query
    await q.edit_message_text(
        "🎮 <b>قائمة الألعاب</b>\n\nاختار اللعبة:",
        parse_mode="HTML",
        reply_markup=games_kb(),
    )


# =========================
# XO
# =========================

def xo_empty():
    return [" "] * 9


def xo_board(board):
    nums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
    cells = []
    for i, x in enumerate(board):
        cells.append(x if x != " " else nums[i])
    return (
        f"{cells[0]} {cells[1]} {cells[2]}\n"
        f"{cells[3]} {cells[4]} {cells[5]}\n"
        f"{cells[6]} {cells[7]} {cells[8]}"
    )


def xo_winner(b):
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for a, c, d in lines:
        if b[a] != " " and b[a] == b[c] == b[d]:
            return b[a]
    if all(x != " " for x in b):
        return "draw"
    return None


def xo_ai_easy(board):
    empty = [i for i, x in enumerate(board) if x == " "]
    return random.choice(empty) if empty else None


def xo_ai_hard(board, ai="⭕", human="❌"):
    def minimax(b, maximizing):
        result = xo_winner(b)
        if result == ai:
            return 10
        if result == human:
            return -10
        if result == "draw":
            return 0

        empty = [i for i, x in enumerate(b) if x == " "]
        scores = []
        for i in empty:
            b[i] = ai if maximizing else human
            scores.append(minimax(b, not maximizing))
            b[i] = " "
        return max(scores) if maximizing else min(scores)

    empty = [i for i, x in enumerate(board) if x == " "]
    if not empty:
        return None

    best_score = -10**9
    best_move = empty[0]
    for i in empty:
        board[i] = ai
        score = minimax(board, False)
        board[i] = " "
        if score > best_score:
            best_score = score
            best_move = i
    return best_move


def xo_buttons(cid):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    str(i + 1), callback_data=f"xom:{cid}:{i}"
                )
                for i in range(3)
            ],
            [
                InlineKeyboardButton(
                    str(i + 1), callback_data=f"xom:{cid}:{i}"
                )
                for i in range(3, 6)
            ],
            [
                InlineKeyboardButton(
                    str(i + 1), callback_data=f"xom:{cid}:{i}"
                )
                for i in range(6, 9)
            ],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


async def xo_start(update, mode, difficulty=None):
    cid = update.effective_chat.id
    if mode == "solo":
        games[cid] = {
            "type": "xo",
            "mode": "solo",
            "board": xo_empty(),
            "turn": "❌",
            "difficulty": difficulty or "easy",
            "user": update.effective_user.id,
        }
        await update.callback_query.edit_message_text(
            "❌⭕ <b>XO</b>\n\n"
            "أنت ❌ والذكاء الاصطناعي ⭕\n\n"
            + xo_board(games[cid]["board"]),
            parse_mode="HTML",
            reply_markup=xo_buttons(cid),
        )
    elif mode == "duo":
        games[cid] = {
            "type": "xo",
            "mode": "duo",
            "board": xo_empty(),
            "turn": "❌",
            "players": [update.effective_user.id],
            "names": {update.effective_user.id: update.effective_user.first_name},
        }
        await update.callback_query.edit_message_text(
            "❌⭕ <b>XO لاعب ضد لاعب</b>\n\n"
            "تم إنشاء اللعبة.\n"
            "اضغط زر الانضمام حتى يدخل اللاعب الثاني.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"xo:join:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )
    else:
        games[cid] = {
            "type": "xo",
            "mode": "tournament",
            "players": [update.effective_user.id],
            "names": {update.effective_user.id: update.effective_user.first_name},
        }
        await update.callback_query.edit_message_text(
            "🏆 <b>بطولة XO</b>\n\n"
            "يجب أن يكون عدد اللاعبين 3 أو 4.\n"
            "أول لاعب ينضم يبدأ البطولة.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"tour:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء البطولة", callback_data=f"tour:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )


async def xo_join(update, context, tournament=False):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)

    if not g:
        await q.answer("اللعبة انتهت.", show_alert=True)
        return

    uid = update.effective_user.id
    if uid in g["players"]:
        await q.answer("أنت منضم بالفعل.")
        return

    if len(g["players"]) >= MAX_PLAYERS:
        await q.answer("اللعبة مكتملة.", show_alert=True)
        return

    g["players"].append(uid)
    g["names"][uid] = update.effective_user.first_name
    await q.answer("تم الانضمام 🎮")

    if tournament:
        await q.edit_message_text(
            "🏆 <b>بطولة XO</b>\n\n"
            + "\n".join(
                f"{i+1}. {g['names'][p]}" for i, p in enumerate(g["players"])
            )
            + "\n\nالحد الأدنى 3 لاعبين.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"tour:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء البطولة", callback_data=f"tour:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )
    elif len(g["players"]) >= 2:
        await q.edit_message_text(
            "❌⭕ <b>XO</b>\n\n"
            f"❌ {g['names'][g['players'][0]]}\n"
            f"⭕ {g['names'][g['players'][1]]}\n\n"
            "ابدأوا اللعب:",
            parse_mode="HTML",
            reply_markup=xo_buttons(cid),
        )


async def xo_finish(update, cid, winner):
    g = games.get(cid)
    if not g:
        return

    if winner == "draw":
        result = "🤝 تعادل!"
    else:
        result = f"🏆 الفائز هو {winner}!"

    games.pop(cid, None)
    await update.callback_query.edit_message_text(
        f"❌⭕ <b>انتهت اللعبة</b>\n\n{result}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:xo")],
                [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
            ]
        ),
    )


async def xo_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)

    if not g or g.get("type") != "xo":
        await q.answer("لا توجد لعبة XO فعالة.", show_alert=True)
        return

    try:
        pos = int(q.data.split(":")[-1])
    except ValueError:
        return

    uid = update.effective_user.id
    if g["mode"] == "solo":
        if uid != g["user"]:
            await q.answer("هذه اللعبة ليست لك.", show_alert=True)
            return
        if g["turn"] != "❌":
            await q.answer("انتظر دورك.")
            return
    else:
        players = g["players"]
        symbol = "❌" if uid == players[0] else "⭕" if uid == players[1] else None
        if symbol is None:
            await q.answer("أنت لست لاعباً في هذه المباراة.", show_alert=True)
            return
        if symbol != g["turn"]:
            await q.answer("مو دورك.")
            return

    if g["board"][pos] != " ":
        await q.answer("هذا المكان مستخدم.")
        return

    g["board"][pos] = g["turn"]
    winner = xo_winner(g["board"])
    if winner:
        await xo_finish(update, cid, winner)
        return

    g["turn"] = "⭕" if g["turn"] == "❌" else "❌"

    if g["mode"] == "solo" and g["turn"] == "⭕":
        ai = (
            xo_ai_hard(g["board"])
            if g["difficulty"] == "hard"
            else xo_ai_easy(g["board"])
        )
        if ai is not None:
            g["board"][ai] = "⭕"
        winner = xo_winner(g["board"])
        if winner:
            await xo_finish(update, cid, winner)
            return
        g["turn"] = "❌"

    if g["mode"] == "solo":
        status = "دورك ❌"
    else:
        current_uid = g["players"][0] if g["turn"] == "❌" else g["players"][1]
        status = f"دور {g['names'][current_uid]} ({g['turn']})"

    await q.edit_message_text(
        "❌⭕ <b>XO</b>\n\n"
        f"{xo_board(g['board'])}\n\n"
        f"🎯 {status}",
        parse_mode="HTML",
        reply_markup=xo_buttons(cid),
    )


# =========================
# XO Tournament
# =========================

def tour_prepare(g):
    players = g["players"][:]
    random.shuffle(players)
    g["round_players"] = players
    g["queue"] = []
    g["waiting"] = None
    g["winners"] = []
    g["match"] = None


async def tour_start(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)

    if not g or g["mode"] != "tournament":
        await q.answer("لا توجد بطولة.", show_alert=True)
        return

    if len(g["players"]) < 3:
        await q.answer("تحتاج البطولة إلى 3 لاعبين على الأقل.", show_alert=True)
        return

    tour_prepare(g)
    await tour_next_match(update, context)


async def tour_next_match(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    # أول جولة
    if g["match"] is None and not g["queue"] and not g["winners"]:
        players = g["round_players"][:]
        while len(players) >= 2:
            a = players.pop(0)
            b = players.pop(0)
            g["queue"].append((a, b))
        if players:
            g["waiting"] = players[0]

    if g["queue"]:
        a, b = g["queue"].pop(0)
        g["match"] = {"a": a, "b": b}
        g["board"] = xo_empty()
        g["turn"] = "❌"
        g["match_players"] = [a, b]
        text = (
            "🏆 <b>بطولة XO</b>\n\n"
            f"⚔️ مباراة: <b>{g['names'][a]}</b> 🆚 <b>{g['names'][b]}</b>\n\n"
            f"{xo_board(g['board'])}\n\n"
            f"🎯 الدور: {g['names'][a]} (❌)"
        )
        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=xo_buttons(cid),
        )
        return

    if g["match"] is None:
        # لا توجد مباريات أخرى في الجولة.
        if g.get("waiting") is not None:
            g["winners"].append(g["waiting"])
            g["waiting"] = None

        if len(g["winners"]) == 1:
            winner_id = g["winners"][0]
            games.pop(cid, None)
            await update.effective_message.reply_text(
                "🏆 <b>انتهت البطولة!</b>\n\n"
                f"🥇 البطل: <b>{g['names'][winner_id]}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🔄 بطولة جديدة", callback_data="game:xo")],
                        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                    ]
                ),
            )
            return

        # جولة جديدة
        g["round_players"] = g["winners"][:]
        g["winners"] = []
        players = g["round_players"][:]
        g["queue"] = []
        while len(players) >= 2:
            g["queue"].append((players.pop(0), players.pop(0)))
        if players:
            g["waiting"] = players[0]
        await tour_next_match(update, context)


async def tour_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)

    if not g or g.get("mode") != "tournament":
        await q.answer("لا توجد مباراة.", show_alert=True)
        return

    try:
        pos = int(q.data.split(":")[-1])
    except ValueError:
        return

    match = g.get("match")
    if not match:
        return

    uid = update.effective_user.id
    a, b = match["a"], match["b"]
    symbol = "❌" if uid == a else "⭕" if uid == b else None

    if symbol is None:
        await q.answer("أنت لست في هذه المباراة.", show_alert=True)
        return

    if symbol != g["turn"]:
        await q.answer("مو دورك.")
        return

    if g["board"][pos] != " ":
        await q.answer("المكان مستخدم.")
        return

    g["board"][pos] = symbol
    winner = xo_winner(g["board"])

    if winner:
        winner_id = a if winner == "❌" else b
        g["winners"].append(winner_id)
        g["match"] = None

        await q.edit_message_text(
            "🏆 <b>نتيجة المباراة</b>\n\n"
            f"الفائز: <b>{g['names'][winner_id]}</b>",
            parse_mode="HTML",
        )
        await tour_next_match(update, context)
        return

    g["turn"] = "⭕" if g["turn"] == "❌" else "❌"
    current = a if g["turn"] == "❌" else b

    await q.edit_message_text(
        "🏆 <b>بطولة XO</b>\n\n"
        f"⚔️ {g['names'][a]} 🆚 {g['names'][b]}\n\n"
        f"{xo_board(g['board'])}\n\n"
        f"🎯 الدور: <b>{g['names'][current]}</b> ({g['turn']})",
        parse_mode="HTML",
        reply_markup=xo_buttons(cid),
    )


# =========================
# RPS
# =========================

RPS = {"rock": "✊", "paper": "📄", "scissors": "✂️"}


def rps_result(a, b):
    if a == b:
        return "draw"
    if (a, b) in [
        ("rock", "scissors"),
        ("scissors", "paper"),
        ("paper", "rock"),
    ]:
        return "a"
    return "b"


def rps_buttons(cid):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✊", callback_data=f"rpsm:{cid}:rock"),
                InlineKeyboardButton("📄", callback_data=f"rpsm:{cid}:paper"),
                InlineKeyboardButton("✂️", callback_data=f"rpsm:{cid}:scissors"),
            ],
            [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
        ]
    )


async def rps_start(update, mode):
    cid = update.effective_chat.id
    uid = update.effective_user.id

    if mode == "solo":
        games[cid] = {
            "type": "rps",
            "mode": "solo",
            "scores": [0, 0],
            "user": uid,
        }
        text = "✊📄✂️ <b>RPS</b>\n\nأول لاعب يصل إلى 3 يفوز!\nاختار:"
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=rps_buttons(cid)
        )
    else:
        games[cid] = {
            "type": "rps",
            "mode": "multi",
            "players": [uid],
            "names": {uid: update.effective_user.first_name},
            "scores": {},
        }
        await update.callback_query.edit_message_text(
            "✊📄✂️ <b>RPS جماعي</b>\n\n"
            "الحد الأقصى 4 لاعبين.\n"
            "انضموا ثم ابدأوا الجولة.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"rps:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء", callback_data=f"rps:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )


async def rps_join(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    uid = update.effective_user.id
    if uid not in g["players"] and len(g["players"]) < MAX_PLAYERS:
        g["players"].append(uid)
        g["names"][uid] = update.effective_user.first_name
        await q.answer("تم الانضمام.")
    else:
        await q.answer("لا يمكن الانضمام.", show_alert=True)

    await q.edit_message_text(
        "✊📄✂️ <b>RPS جماعي</b>\n\n"
        + "\n".join(
            f"{i+1}. {g['names'][p]}" for i, p in enumerate(g["players"])
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ انضمام", callback_data=f"rps:join:{cid}")],
                [InlineKeyboardButton("▶️ بدء", callback_data=f"rps:start:{cid}")],
                [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
            ]
        ),
    )


async def rps_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    choice = q.data.split(":")[-1]
    uid = update.effective_user.id

    if g["mode"] == "solo":
        if uid != g["user"]:
            await q.answer("هذه اللعبة ليست لك.", show_alert=True)
            return
        ai = random.choice(list(RPS))
        res = rps_result(choice, ai)
        if res == "a":
            g["scores"][0] += 1
        elif res == "b":
            g["scores"][1] += 1

        if max(g["scores"]) >= 3:
            winner = "🎉 أنت الفائز!" if g["scores"][0] >= 3 else "🤖 الـAI فاز!"
            games.pop(cid, None)
            await q.edit_message_text(
                f"✊📄✂️ <b>انتهت الجولة</b>\n\n"
                f"أنت: {RPS[choice]}\nAI: {RPS[ai]}\n\n"
                f"{winner}",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:rps")],
                        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                    ]
                ),
            )
            return

        await q.edit_message_text(
            f"✊📄✂️ <b>RPS</b>\n\n"
            f"أنت: {RPS[choice]}\nAI: {RPS[ai]}\n\n"
            f"النتيجة: {g['scores'][0]} - {g['scores'][1]}\n\nاختار:",
            parse_mode="HTML",
            reply_markup=rps_buttons(cid),
        )
    else:
        # كل لاعب يختار، ثم نحسب الجولة عندما يكتمل الاختيار.
        if uid not in g["players"]:
            await q.answer("أنت لست لاعباً.", show_alert=True)
            return
        g.setdefault("choices", {})[uid] = choice

        await q.answer("تم تسجيل اختيارك.")
        if len(g["choices"]) < len(g["players"]):
            return

        choices = g["choices"]
        # نحسب الفائزين بحسب اختيار كل لاعب ضد الآخرين.
        points = {p: 0 for p in g["players"]}
        for p in g["players"]:
            for other in g["players"]:
                if p == other:
                    continue
                r = rps_result(choices[p], choices[other])
                if r == "a":
                    points[p] += 1

        best = max(points.values())
        winners = [p for p, score in points.items() if score == best]
        if len(winners) == 1:
            winner_id = winners[0]
            games.pop(cid, None)
            result = f"🏆 الفائز: {g['names'][winner_id]}"
        else:
            result = "🤝 تعادل: " + ", ".join(g["names"][p] for p in winners)

        await q.edit_message_text(
            "✊📄✂️ <b>نتيجة الجولة</b>\n\n"
            + "\n".join(
                f"• {g['names'][p]}: {RPS[choices[p]]}"
                for p in g["players"]
            )
            + f"\n\n{result}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")]]
            ),
        )


async def rps_start_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g or len(g["players"]) < 2:
        await update.callback_query.answer(
            "لازم لاعبين على الأقل.", show_alert=True
        )
        return

    g["choices"] = {}
    await update.callback_query.edit_message_text(
        "✊📄✂️ <b>RPS جماعي</b>\n\nكل لاعب يختار اختياره:",
        parse_mode="HTML",
        reply_markup=rps_buttons(cid),
    )


# =========================
# Guess Number
# =========================

def guess_buttons(cid, low=1, high=50):
    # أزرار رقمية مقسمة إلى صفحات صغيرة، مع إمكانية التخمين بالنقر.
    # نطاق اللعبة 1-50.
    rows = []
    nums = list(range(low, high + 1))
    for i in range(0, len(nums), 5):
        rows.append(
            [
                InlineKeyboardButton(str(n), callback_data=f"guessm:{cid}:{n}")
                for n in nums[i:i + 5]
            ]
        )
    rows.append([InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")])
    return InlineKeyboardMarkup(rows)


async def guess_start(update, mode):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if mode == "solo":
        games[cid] = {
            "type": "guess",
            "mode": "solo",
            "number": random.randint(1, 50),
            "tries": GUESS_TRIES,
            "user": uid,
        }
        await update.callback_query.edit_message_text(
            "🔢 <b>خمن الرقم</b>\n\n"
            "الرقم بين 1 و50.\n"
            f"عندك {GUESS_TRIES} محاولات.\n\nاختار رقم:",
            parse_mode="HTML",
            reply_markup=guess_buttons(cid),
        )
    else:
        games[cid] = {
            "type": "guess",
            "mode": "multi",
            "number": random.randint(1, 50),
            "tries": {},
            "players": [uid],
            "names": {uid: update.effective_user.first_name},
        }
        await update.callback_query.edit_message_text(
            "🔢 <b>خمن الرقم جماعي</b>\n\n"
            "ينضم 2-4 لاعبين، وكل لاعب عنده محاولاته.\n\n"
            "اضغط انضمام:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"guess:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء", callback_data=f"guess:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )


async def guess_join(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    uid = update.effective_user.id
    if uid not in g["players"] and len(g["players"]) < MAX_PLAYERS:
        g["players"].append(uid)
        g["names"][uid] = update.effective_user.first_name
        await q.answer("تم الانضمام.")
    else:
        await q.answer("لا يمكن الانضمام.", show_alert=True)

    await q.edit_message_text(
        "🔢 <b>خمن الرقم جماعي</b>\n\n"
        + "\n".join(
            f"{i+1}. {g['names'][p]}" for i, p in enumerate(g["players"])
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ انضمام", callback_data=f"guess:join:{cid}")],
                [InlineKeyboardButton("▶️ بدء", callback_data=f"guess:start:{cid}")],
                [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
            ]
        ),
    )


async def guess_start_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g or len(g["players"]) < 2:
        await update.callback_query.answer(
            "لازم لاعبين على الأقل.", show_alert=True
        )
        return

    g["tries"] = {p: GUESS_TRIES for p in g["players"]}
    await update.callback_query.edit_message_text(
        "🔢 <b>خمن الرقم</b>\n\n"
        "كل لاعب يختار رقم. أول واحد يصيب يفوز.\n\nاختار:",
        parse_mode="HTML",
        reply_markup=guess_buttons(cid),
    )


async def guess_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    try:
        n = int(q.data.split(":")[-1])
    except ValueError:
        return

    uid = update.effective_user.id
    if g["mode"] == "solo":
        if uid != g["user"]:
            await q.answer("هذه اللعبة ليست لك.", show_alert=True)
            return
        remaining = g["tries"]
    else:
        if uid not in g["players"]:
            await q.answer("أنت لست لاعباً.", show_alert=True)
            return
        remaining = g["tries"].get(uid, 0)

    if remaining <= 0:
        await q.answer("خلصت محاولاتك.")
        return

    if n == g["number"]:
        winner_name = "أنت" if g["mode"] == "solo" else g["names"][uid]
        games.pop(cid, None)
        await q.edit_message_text(
            "🎉 <b>مبروك!</b>\n\n"
            f"🏆 {winner_name} خمن الرقم الصحيح: <b>{n}</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:guess")],
                    [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                ]
            ),
        )
        return

    if g["mode"] == "solo":
        g["tries"] -= 1
        remaining = g["tries"]
    else:
        g["tries"][uid] -= 1
        remaining = g["tries"][uid]

    hint = "⬆️ الرقم أكبر" if n < g["number"] else "⬇️ الرقم أصغر"

    if g["mode"] == "solo" and remaining <= 0:
        number = g["number"]
        games.pop(cid, None)
        await q.edit_message_text(
            f"❌ <b>خلصت المحاولات</b>\n\nالرقم كان: <b>{number}</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:guess")],
                    [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                ]
            ),
        )
        return

    await q.edit_message_text(
        "🔢 <b>خمن الرقم</b>\n\n"
        f"{hint}\n"
        f"باقي محاولاتك: <b>{remaining}</b>\n\nاختار:",
        parse_mode="HTML",
        reply_markup=guess_buttons(cid),
    )


# =========================
# Animals
# =========================

ANIMALS = [
    ("🐱", "قط", ["قط", "قطة"]),
    ("🐶", "كلب", ["كلب", "جرو"]),
    ("🦁", "أسد", ["أسد", "اسد"]),
    ("🐘", "فيل", ["فيل"]),
    ("🐴", "حصان", ["حصان"]),
    ("🐰", "أرنب", ["أرنب", "ارنب"]),
    ("🐼", "باندا", ["باندا"]),
    ("🦊", "ثعلب", ["ثعلب"]),
    ("🐯", "نمر", ["نمر"]),
    ("🐵", "قرد", ["قرد"]),
]


def animal_question(g):
    emoji, answer, aliases = random.choice(ANIMALS)
    g["current"] = {"emoji": emoji, "answer": answer, "aliases": aliases}
    return (
        f"🐾 <b>شنو هذا الحيوان؟</b>\n\n"
        f"{emoji}\n\n"
        "اختار الإجابة:"
    )


def animal_choices(g):
    current = g["current"]["answer"]
    others = [a[1] for a in ANIMALS if a[1] != current]
    opts = [current] + random.sample(others, 2)
    random.shuffle(opts)
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(x, callback_data=f"animalm:{g['cid']}:{x}")]
            for x in opts
        ] + [[InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")]]
    )


async def animal_start(update, mode):
    cid = update.effective_chat.id
    uid = update.effective_user.id

    if mode == "solo":
        games[cid] = {
            "type": "animal",
            "mode": "solo",
            "user": uid,
            "q": 0,
            "score": 0,
            "cid": cid,
        }
        g = games[cid]
        text = animal_question(g)
        await update.callback_query.edit_message_text(
            text, parse_mode="HTML", reply_markup=animal_choices(g)
        )
    else:
        games[cid] = {
            "type": "animal",
            "mode": "multi",
            "players": [uid],
            "names": {uid: update.effective_user.first_name},
            "cid": cid,
            "q": 0,
            "scores": {},
        }
        await update.callback_query.edit_message_text(
            "🐾 <b>الحيوانات جماعي</b>\n\n"
            "2-4 لاعبين.\n"
            "كل لاعب يجاوب على الأسئلة.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"animal:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء", callback_data=f"animal:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )


async def animal_join(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return
    uid = update.effective_user.id
    if uid not in g["players"] and len(g["players"]) < MAX_PLAYERS:
        g["players"].append(uid)
        g["names"][uid] = update.effective_user.first_name
        await q.answer("تم الانضمام.")
    await q.edit_message_text(
        "🐾 <b>الحيوانات جماعي</b>\n\n"
        + "\n".join(
            f"{i+1}. {g['names'][p]}" for i, p in enumerate(g["players"])
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ انضمام", callback_data=f"animal:join:{cid}")],
                [InlineKeyboardButton("▶️ بدء", callback_data=f"animal:start:{cid}")],
                [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
            ]
        ),
    )


async def animal_start_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g or len(g["players"]) < 2:
        await update.callback_query.answer(
            "لازم لاعبين على الأقل.", show_alert=True
        )
        return
    g["scores"] = {p: 0 for p in g["players"]}
    g["round"] = 0
    g["current_player_index"] = 0
    await animal_next_multi(update, context)


async def animal_next_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    if g["round"] >= AN_MULTI_PP:
        winner_score = max(g["scores"].values())
        winners = [p for p, s in g["scores"].items() if s == winner_score]
        result = (
            "🤝 تعادل!"
            if len(winners) > 1
            else f"🏆 الفائز: {g['names'][winners[0]]}"
        )
        games.pop(cid, None)
        await update.effective_message.reply_text(
            "🐾 <b>انتهت الحيوانات</b>\n\n"
            + "\n".join(
                f"• {g['names'][p]}: {g['scores'][p]}"
                for p in g["players"]
            )
            + f"\n\n{result}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")]]
            ),
        )
        return

    player = g["players"][g["current_player_index"]]
    g["active_player"] = player
    g["current"] = None
    text = animal_question(g)
    await update.effective_message.reply_text(
        f"🐾 <b>دور {g['names'][player]}</b>\n\n{text}",
        parse_mode="HTML",
        reply_markup=animal_choices(g),
    )


async def animal_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    answer = q.data.split(":", 2)[-1]
    uid = update.effective_user.id

    if g["mode"] == "solo":
        if uid != g["user"]:
            await q.answer("هذه اللعبة ليست لك.", show_alert=True)
            return
        correct = answer in g["current"]["aliases"]
        if correct:
            g["score"] += 1
        g["q"] += 1

        if g["q"] >= AN_SOLO:
            score = g["score"]
            games.pop(cid, None)
            await q.edit_message_text(
                f"🐾 <b>انتهت اللعبة!</b>\n\nنتيجتك: <b>{score}/{AN_SOLO}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:animal")],
                        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                    ]
                ),
            )
            return

        text = animal_question(g)
        await q.edit_message_text(
            f"{'✅ صحيح!' if correct else '❌ خطأ!'}\n\n{text}",
            parse_mode="HTML",
            reply_markup=animal_choices(g),
        )
    else:
        player = g.get("active_player")
        if uid != player:
            await q.answer("انتظر دور اللاعب الحالي.")
            return

        correct = answer in g["current"]["aliases"]
        if correct:
            g["scores"][uid] += 1

        g["current_player_index"] += 1
        if g["current_player_index"] >= len(g["players"]):
            g["current_player_index"] = 0
            g["round"] += 1

        await q.answer("✅ صحيح!" if correct else "❌ خطأ!")
        await animal_next_multi(update, context)


# =========================
# Ladder
# =========================

LADDER_Q = [
    ("عاصمة العراق؟", ["بغداد", "البصرة", "الموصل"], "بغداد"),
    ("أكبر كوكب؟", ["المشتري", "المريخ", "الأرض"], "المشتري"),
    ("كم عدد أيام الأسبوع؟", ["7", "5", "10"], "7"),
    ("ما لون الموز غالباً؟", ["أصفر", "أزرق", "أسود"], "أصفر"),
    ("كم ضلع للمثلث؟", ["3", "4", "5"], "3"),
    ("الكوكب الأحمر؟", ["المريخ", "الزهرة", "عطارد"], "المريخ"),
    ("أسرع حيوان بري؟", ["الفهد", "الفيل", "الحصان"], "الفهد"),
    ("أكبر محيط؟", ["الهادئ", "الأطلسي", "الهندي"], "الهادئ"),
    ("كم ساعة في اليوم؟", ["24", "12", "48"], "24"),
    ("ما عكس كلمة كبير؟", ["صغير", "طويل", "سريع"], "صغير"),
]


def ladder_question(g):
    q = random.choice(LADDER_Q)
    g["current"] = q
    question, options, answer = q
    rows = [
        [InlineKeyboardButton(o, callback_data=f"ladderm:{g['cid']}:{o}")]
        for o in options
    ]
    rows.append([InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")])
    return question, InlineKeyboardMarkup(rows)


async def ladder_start(update, mode):
    cid = update.effective_chat.id
    uid = update.effective_user.id
    if mode == "solo":
        games[cid] = {
            "type": "ladder",
            "mode": "solo",
            "user": uid,
            "level": 0,
            "score": 0,
            "cid": cid,
        }
        g = games[cid]
        question, kb = ladder_question(g)
        await update.callback_query.edit_message_text(
            f"🪜 <b>السلم</b>\n\n"
            f"المستوى: 1/{LADDER_TARGET}\n\n"
            f"❓ {question}",
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        games[cid] = {
            "type": "ladder",
            "mode": "multi",
            "players": [uid],
            "names": {uid: update.effective_user.first_name},
            "scores": {},
            "cid": cid,
        }
        await update.callback_query.edit_message_text(
            "🪜 <b>السلم جماعي</b>\n\n"
            "2-4 لاعبين.\n"
            "انضموا ثم ابدأوا.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("➕ انضمام", callback_data=f"ladder:join:{cid}")],
                    [InlineKeyboardButton("▶️ بدء", callback_data=f"ladder:start:{cid}")],
                    [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
                ]
            ),
        )


async def ladder_join(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return
    uid = update.effective_user.id
    if uid not in g["players"] and len(g["players"]) < MAX_PLAYERS:
        g["players"].append(uid)
        g["names"][uid] = update.effective_user.first_name
        await q.answer("تم الانضمام.")
    await q.edit_message_text(
        "🪜 <b>السلم جماعي</b>\n\n"
        + "\n".join(
            f"{i+1}. {g['names'][p]}" for i, p in enumerate(g["players"])
        ),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("➕ انضمام", callback_data=f"ladder:join:{cid}")],
                [InlineKeyboardButton("▶️ بدء", callback_data=f"ladder:start:{cid}")],
                [InlineKeyboardButton("🔙 الألعاب", callback_data="games_menu")],
            ]
        ),
    )


async def ladder_start_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g or len(g["players"]) < 2:
        await update.callback_query.answer(
            "لازم لاعبين على الأقل.", show_alert=True
        )
        return
    g["scores"] = {p: 0 for p in g["players"]}
    g["round"] = 0
    g["current_player_index"] = 0
    await ladder_next_multi(update, context)


async def ladder_next_multi(update, context):
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    if g["round"] >= LADDER_TARGET:
        best = max(g["scores"].values())
        winners = [p for p, s in g["scores"].items() if s == best]
        result = (
            "🤝 تعادل!"
            if len(winners) > 1
            else f"🏆 الفائز: {g['names'][winners[0]]}"
        )
        games.pop(cid, None)
        await update.effective_message.reply_text(
            "🪜 <b>انتهى السلم</b>\n\n"
            + "\n".join(
                f"• {g['names'][p]}: {g['scores'][p]}"
                for p in g["players"]
            )
            + f"\n\n{result}",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")]]
            ),
        )
        return

    player = g["players"][g["current_player_index"]]
    g["active_player"] = player
    question, kb = ladder_question(g)
    await update.effective_message.reply_text(
        f"🪜 <b>دور {g['names'][player]}</b>\n\n"
        f"المستوى: {g['round'] + 1}/{LADDER_TARGET}\n\n"
        f"❓ {question}",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def ladder_move(update, context):
    q = update.callback_query
    cid = update.effective_chat.id
    g = games.get(cid)
    if not g:
        return

    answer = q.data.split(":", 2)[-1]
    uid = update.effective_user.id

    if g["mode"] == "solo":
        if uid != g["user"]:
            await q.answer("هذه اللعبة ليست لك.", show_alert=True)
            return
        question, options, correct = g["current"]
        is_correct = answer == correct

        if is_correct:
            g["score"] += 1
            g["level"] += 1
        else:
            g["level"] += 1

        if g["level"] >= LADDER_TARGET:
            score = g["score"]
            games.pop(cid, None)
            await q.edit_message_text(
                f"🪜 <b>انتهى السلم</b>\n\n"
                f"نتيجتك: <b>{score}/{LADDER_TARGET}</b>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("🔄 لعبة جديدة", callback_data="game:ladder")],
                        [InlineKeyboardButton("🎮 الألعاب", callback_data="games_menu")],
                    ]
                ),
            )
            return

        question, kb = ladder_question(g)
        await q.edit_message_text(
            f"{'✅ صحيح!' if is_correct else '❌ خطأ!'}\n\n"
            f"🪜 المستوى: {g['level'] + 1}/{LADDER_TARGET}\n\n"
            f"❓ {question}",
            parse_mode="HTML",
            reply_markup=kb,
        )
    else:
        player = g.get("active_player")
        if uid != player:
            await q.answer("انتظر دور اللاعب الحالي.")
            return

        question, options, correct = g["current"]
        if answer == correct:
            g["scores"][uid] += 1

        g["current_player_index"] += 1
        if g["current_player_index"] >= len(g["players"]):
            g["current_player_index"] = 0
            g["round"] += 1

        await q.answer("✅ صحيح!" if answer == correct else "❌ خطأ!")
        await ladder_next_multi(update, context)


# =========================
# Router
# =========================

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data or ""

    # دائماً نجاوب callback حتى لا يبقى زر التحميل.
    await q.answer()

    if data == "main_menu":
        await show_main(update)
        return

    if data == "games_menu" or data == "call_games":
        await show_games(update, context)
        return

    if data == "activate":
        await activate_chat(update, context)
        return

    # الألعاب
    if data == "game:xo":
        if await require_activation(update, context):
            await q.edit_message_text(
                "❌⭕ <b>XO</b>\n\nاختار طريقة اللعب:",
                parse_mode="HTML",
                reply_markup=xo_mode_kb(),
            )
        return

    if data == "game:rps":
        if await require_activation(update, context):
            await q.edit_message_text(
                "✊📄✂️ <b>RPS</b>\n\nاختار:",
                parse_mode="HTML",
                reply_markup=rps_mode_kb(),
            )
        return

    if data == "game:guess":
        if await require_activation(update, context):
            await q.edit_message_text(
                "🔢 <b>خمن الرقم</b>\n\nاختار:",
                parse_mode="HTML",
                reply_markup=guess_mode_kb(),
            )
        return

    if data == "game:animal":
        if await require_activation(update, context):
            await q.edit_message_text(
                "🐾 <b>الحيوانات</b>\n\nاختار:",
                parse_mode="HTML",
                reply_markup=animal_mode_kb(),
            )
        return

    if data == "game:ladder":
        if await require_activation(update, context):
            await q.edit_message_text(
                "🪜 <b>السلم</b>\n\nاختار:",
                parse_mode="HTML",
                reply_markup=ladder_mode_kb(),
            )
        return

    # XO
    if data == "xo:solo:easy":
        await xo_start(update, "solo", "easy")
        return
    if data == "xo:solo:hard":
        await xo_start(update, "solo", "hard")
        return
    if data == "xo:duo":
        await xo_start(update, "duo")
        return
    if data == "xo:tournament":
        await xo_start(update, "tournament")
        return
    if data.startswith("xo:join:"):
        await xo_join(update, context, tournament=False)
        return
    if data.startswith("tour:join:"):
        await xo_join(update, context, tournament=True)
        return
    if data.startswith("tour:start:"):
        await tour_start(update, context)
        return
    if data.startswith("xom:"):
        cid = update.effective_chat.id
        g = games.get(cid)
        if g and g.get("mode") == "tournament":
            await tour_move(update, context)
        else:
            await xo_move(update, context)
        return

    # RPS
    if data == "rps:solo":
        await rps_start(update, "solo")
        return
    if data == "rps:multi":
        await rps_start(update, "multi")
        return
    if data.startswith("rps:join:"):
        await rps_join(update, context)
        return
    if data.startswith("rps:start:"):
        await rps_start_multi(update, context)
        return
    if data.startswith("rpsm:"):
        await rps_move(update, context)
        return

    # Guess
    if data == "guess:solo":
        await guess_start(update, "solo")
        return
    if data == "guess:multi":
        await guess_start(update, "multi")
        return
    if data.startswith("guess:join:"):
        await guess_join(update, context)
        return
    if data.startswith("guess:start:"):
        await guess_start_multi(update, context)
        return
    if data.startswith("guessm:"):
        await guess_move(update, context)
        return

    # Animals
    if data == "animal:solo":
        await animal_start(update, "solo")
        return
    if data == "animal:multi":
        await animal_start(update, "multi")
        return
    if data.startswith("animal:join:"):
        await animal_join(update, context)
        return
    if data.startswith("animal:start:"):
        await animal_start_multi(update, context)
        return
    if data.startswith("animalm:"):
        await animal_move(update, context)
        return

    # Ladder
    if data == "ladder:solo":
        await ladder_start(update, "solo")
        return
    if data == "ladder:multi":
        await ladder_start(update, "multi")
        return
    if data.startswith("ladder:join:"):
        await ladder_join(update, context)
        return
    if data.startswith("ladder:start:"):
        await ladder_start_multi(update, context)
        return
    if data.startswith("ladderm:"):
        await ladder_move(update, context)
        return


def _render_keepalive():
    """HTTP server صغير داخل نفس الملف لتشغيله كـ Render Web Service."""
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = b"Game Bot is running"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            return

    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"🌐 Render web server running on port {port}")


def main():
    if not BOT_TOKEN or BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("⚠️ ضع توكن البوت في BOT_TOKEN أو متغير البيئة BOT_TOKEN.")
        return

    _render_keepalive()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dev", dev))
    app.add_handler(CallbackQueryHandler(callbacks))

    print("🎮 Game Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
