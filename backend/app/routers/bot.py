import hmac

from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request

router = APIRouter()


@router.post("/bot/webhook/{secret}")
async def webhook(
    secret: str,
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    expected = request.app.state.settings.webhook_secret
    if not hmac.compare_digest(secret, expected):
        raise HTTPException(404)
    if x_telegram_bot_api_secret_token is not None and not hmac.compare_digest(
        x_telegram_bot_api_secret_token, expected
    ):
        raise HTTPException(403)
    bot, dp = request.app.state.bot, request.app.state.dp
    if bot is None or dp is None:
        raise HTTPException(503, "Bot disabled")
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}
