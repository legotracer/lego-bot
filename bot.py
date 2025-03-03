import sys
sys.stdout.reconfigure(encoding='utf-8')  # UTF-8 인코딩 적용
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from scraper import get_coupang_price, get_lego_price  # 🔹 쿠팡 + 레고몰 가격만 가져오도록 수정

TOKEN = "8165700117:AAH0IjNbQsxJ1SRI5Wr4Vo1rdepeFeURdtc"

async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "안녕하세요! 레고 가격 추적 봇입니다. 🏗️\n"
        "레고 모델 번호를 입력하면 가격을 조회할 수 있어요.\n"
        "예: `/lego 75313`"
    )

async def lego(update: Update, context: CallbackContext) -> None:
    if len(context.args) == 0:
        await update.message.reply_text("레고 모델 번호를 입력해주세요! 예: `/lego 75313`")
        return

    lego_number = context.args[0]  
    coupang_price = get_coupang_price(lego_number)  
    lego_price = get_lego_price(lego_number)  

    response = f"**레고 {lego_number} 가격 정보**\n"
    response += f"1) **쿠팡**: {coupang_price}\n"
    response += f"2) **레고 공식몰**: {lego_price}\n"

    await update.message.reply_text(response, parse_mode="Markdown")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("lego", lego))

    application.run_polling()

if __name__ == "__main__":
    main()
