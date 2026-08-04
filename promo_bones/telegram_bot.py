"""Integração com Telegram Bot API (síncrono com requests)."""
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_ID
from database import SessionLocal, PromoMessage

TELEGRAM_API = "https://api.telegram.org"


def send_text_sync(text: str, chat_id: str = None, parse_mode: str = "HTML") -> dict:
    """Envia mensagem de texto de forma síncrona."""
    token = TELEGRAM_BOT_TOKEN
    target = chat_id or TELEGRAM_GROUP_ID
    if not token:
        return {"ok": False, "description": "Token não configurado"}
    if not target:
        return {"ok": False, "description": "Chat ID não configurado"}

    url = f"{TELEGRAM_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": target,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def send_photo_sync(photo_url: str, caption: str, chat_id: str = None, parse_mode: str = "HTML") -> dict:
    """Envia foto com legenda de forma síncrona."""
    token = TELEGRAM_BOT_TOKEN
    target = chat_id or TELEGRAM_GROUP_ID
    if not token:
        return {"ok": False, "description": "Token não configurado"}
    if not target:
        return {"ok": False, "description": "Chat ID não configurado"}

    url = f"{TELEGRAM_API}/bot{token}/sendPhoto"
    payload = {
        "chat_id": target,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": parse_mode,
    }
    try:
        resp = requests.post(url, json=payload, timeout=30)
        return resp.json()
    except Exception as e:
        return {"ok": False, "description": str(e)}


def check_bot_config_sync() -> dict:
    """Verifica se o bot está configurado corretamente."""
    if not TELEGRAM_BOT_TOKEN:
        return {"configured": False, "error": "Token do bot não configurado"}

    url = f"{TELEGRAM_API}/bot{TELEGRAM_BOT_TOKEN}/getMe"
    try:
        resp = requests.get(url, timeout=10)
        result = resp.json()
        if result.get("ok"):
            bot_info = result["result"]
            return {
                "configured": True,
                "bot_name": bot_info.get("first_name"),
                "bot_username": bot_info.get("username"),
                "group_id": TELEGRAM_GROUP_ID if TELEGRAM_GROUP_ID else None,
            }
        return {"configured": False, "error": result.get("description", "Erro na API")}
    except Exception as e:
        return {"configured": False, "error": str(e)}


def send_promo_message_sync(message_id: int, chat_id: str = None) -> dict:
    """Envia uma mensagem de promoção salva no banco para o Telegram."""
    db = SessionLocal()
    try:
        msg = db.query(PromoMessage).filter(PromoMessage.id == message_id).first()
        if not msg:
            return {"success": False, "error": "Mensagem não encontrada"}

        target = chat_id or TELEGRAM_GROUP_ID
        if not target:
            return {"success": False, "error": "Chat ID não configurado"}

        if msg.image_url:
            result = send_photo_sync(msg.image_url, msg.content, target)
        else:
            result = send_text_sync(msg.content, target)

        if result.get("ok"):
            msg.status = "sent"
            msg.telegram_message_id = result["result"]["message_id"]
            db.commit()
            return {"success": True, "telegram_message_id": result["result"]["message_id"]}
        else:
            msg.status = "error"
            db.commit()
            return {"success": False, "error": result.get("description", "Erro desconhecido")}
    finally:
        db.close()
