"""Utya Gift Price Bot — aggregates gift prices across GetGems, Fragment, MRKT, Portals, Tonnel."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
from gifts import GIFTS, Gift
from parsers.aggregator import fetch_all_prices, fetch_gift_prices, invalidate_cache, sort_by_best_deal
from parsers.base import AggregatedPrice, Platform, PLATFORM_EMOJI

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

router = Router()

# ─── Formatting helpers ───────────────────────────────────────────────────────

def _fmt_ton(price: float) -> str:
    return f"{price:.2f} TON"


def _platform_line(result, best_price: float | None) -> str:
    em = PLATFORM_EMOJI[result.platform]
    name = result.platform.value
    if not result.available:
        return f"{em} {name:<10} —"
    price_str = _fmt_ton(result.price_ton)
    star = " ✅" if (best_price is not None and abs(result.price_ton - best_price) < 0.001) else ""
    return f"{em} {name:<10} {price_str}{star}"


def _build_gift_message(agg: AggregatedPrice) -> str:
    lines = [f"<b>{agg.gift.display_name}</b>\n"]

    for result in agg.results:
        lines.append(_platform_line(result, agg.best_price))

    best = agg.best_result
    avg = agg.avg_price
    lines.append("")

    if best and best.price_ton is not None:
        deal_line = f"💰 Best: <b>{_fmt_ton(best.price_ton)}</b> on <b>{best.platform.value}</b>"
        if avg and avg > 0:
            pct = (avg - best.price_ton) / avg * 100
            if pct >= 1:
                deal_line += f" ({pct:.1f}% below avg)"
        lines.append(deal_line)
    else:
        lines.append("❌ No listings found on any platform")

    return "\n".join(lines)


def _build_summary_message(aggregated: list[AggregatedPrice]) -> str:
    sorted_agg = sort_by_best_deal(aggregated)
    lines = ["<b>📊 Best Deals — All Gifts</b>\n"]

    for i, agg in enumerate(sorted_agg, 1):
        best = agg.best_result
        avg = agg.avg_price
        if best and best.price_ton is not None:
            deal_info = f"{_fmt_ton(best.price_ton)} {PLATFORM_EMOJI[best.platform]}{best.platform.value}"
            if avg and avg > 0:
                pct = (avg - best.price_ton) / avg * 100
                if pct >= 1:
                    deal_info += f" (−{pct:.1f}%)"
            lines.append(f"{i}. {agg.gift.display_name}\n   └ {deal_info}")
        else:
            lines.append(f"{i}. {agg.gift.display_name}\n   └ No data")

    return "\n".join(lines)


# ─── Keyboard builders ────────────────────────────────────────────────────────

def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Best Deals (all gifts)", callback_data="summary")],
        [InlineKeyboardButton(text="🔍 Check a specific gift", callback_data="gift_list:0")],
    ])


def _gift_list_keyboard(page: int = 0) -> InlineKeyboardMarkup:
    per_page = 8
    start = page * per_page
    end = min(start + per_page, len(GIFTS))
    buttons: list[list[InlineKeyboardButton]] = []

    for i in range(start, end):
        gift = GIFTS[i]
        buttons.append([
            InlineKeyboardButton(
                text=gift.display_name,
                callback_data=f"gift:{i}",
            )
        ])

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀ Prev", callback_data=f"gift_list:{page - 1}"))
    if end < len(GIFTS):
        nav.append(InlineKeyboardButton(text="Next ▶", callback_data=f"gift_list:{page + 1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="🏠 Main menu", callback_data="main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _gift_detail_keyboard(gift_index: int, page: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh prices", callback_data=f"refresh:{gift_index}")],
        [InlineKeyboardButton(text="◀ Back to list", callback_data=f"gift_list:{page}")],
        [InlineKeyboardButton(text="🏠 Main menu", callback_data="main")],
    ])


def _summary_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Refresh all", callback_data="refresh_summary")],
        [InlineKeyboardButton(text="🏠 Main menu", callback_data="main")],
    ])


# ─── Handlers ─────────────────────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 <b>Utya Gift Price Bot</b>\n\n"
        "I track Telegram gift prices across:\n"
        "💎 GetGems  •  🔷 Fragment\n"
        "🔥 MRKT  •  🌀 Portals  •  ⚡ Tonnel\n\n"
        "Find the best deal instantly!",
        reply_markup=_main_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("prices"))
async def cmd_prices(message: Message) -> None:
    msg = await message.answer("⏳ Fetching prices from all platforms…")
    aggregated = await fetch_all_prices()
    text = _build_summary_message(aggregated)
    await msg.edit_text(text, reply_markup=_summary_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "main")
async def cb_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "👋 <b>Utya Gift Price Bot</b>\n\n"
        "I track Telegram gift prices across:\n"
        "💎 GetGems  •  🔷 Fragment\n"
        "🔥 MRKT  •  🌀 Portals  •  ⚡ Tonnel\n\n"
        "Find the best deal instantly!",
        reply_markup=_main_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "summary")
async def cb_summary(callback: CallbackQuery) -> None:
    await callback.message.edit_text("⏳ Fetching prices from all platforms…")
    aggregated = await fetch_all_prices()
    text = _build_summary_message(aggregated)
    await callback.message.edit_text(text, reply_markup=_summary_keyboard(), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "refresh_summary")
async def cb_refresh_summary(callback: CallbackQuery) -> None:
    await callback.message.edit_text("🔄 Refreshing all prices…")
    invalidate_cache()
    aggregated = await fetch_all_prices(use_cache=False)
    text = _build_summary_message(aggregated)
    await callback.message.edit_text(text, reply_markup=_summary_keyboard(), parse_mode="HTML")
    await callback.answer("✅ Prices refreshed!")


@router.callback_query(F.data.startswith("gift_list:"))
async def cb_gift_list(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await callback.message.edit_text(
        "🔍 <b>Select a gift to check prices:</b>",
        reply_markup=_gift_list_keyboard(page),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("gift:"))
async def cb_gift_detail(callback: CallbackQuery) -> None:
    gift_index = int(callback.data.split(":")[1])
    gift = GIFTS[gift_index]
    await callback.message.edit_text(f"⏳ Fetching prices for {gift.display_name}…")
    agg = await fetch_gift_prices(gift)
    text = _build_gift_message(agg)
    await callback.message.edit_text(
        text,
        reply_markup=_gift_detail_keyboard(gift_index),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("refresh:"))
async def cb_refresh_gift(callback: CallbackQuery) -> None:
    gift_index = int(callback.data.split(":")[1])
    gift = GIFTS[gift_index]
    await callback.message.edit_text(f"🔄 Refreshing prices for {gift.display_name}…")
    agg = await fetch_gift_prices(gift, use_cache=False)
    text = _build_gift_message(agg)
    await callback.message.edit_text(
        text,
        reply_markup=_gift_detail_keyboard(gift_index),
        parse_mode="HTML",
    )
    await callback.answer("✅ Prices refreshed!")


# ─── Entry point ──────────────────────────────────────────────────────────────

async def main() -> None:
    bot = Bot(token=config.BOT_TOKEN, parse_mode="HTML")
    dp = Dispatcher()
    dp.include_router(router)
    logger.info("Starting Utya Gift Price Bot…")
    await dp.start_polling(bot, skip_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
