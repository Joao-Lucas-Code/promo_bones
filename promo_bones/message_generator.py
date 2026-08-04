"""Geração de mensagens no formato dos grupos de promoção."""
import html
from datetime import datetime
from typing import Optional

from config import AFFILIATE_CONFIG
from database import Product, Coupon, SessionLocal


class MessageGenerator:
    """Gera mensagens formatadas para Telegram (HTML parse mode)."""

    @staticmethod
    def _escape(text: str) -> str:
        """Escapa caracteres especiais do HTML do Telegram."""
        return html.escape(str(text), quote=False)

    @staticmethod
    def generate_product_message(product: Product, coupon: Optional[Coupon] = None) -> dict:
        """Gera uma mensagem no estilo dos grupos de promoção.

        Formato baseado nos prints do usuário:
        - Headline chamativa em CAIXA ALTA
        - Nome do produto
        - Preço original riscado
        - Preço atual
        - Cupom (se houver)
        - Link de compra
        """

        # Escolhe headline baseado no desconto
        discount = product.discount_percent or 0
        if discount >= 50:
            headline = "🎯 MENOR PREÇO HISTÓRICO"
        elif discount >= 40:
            headline = "⚡ VOLTOU! ESSE SEMPRE ESGOTA RÁPIDO"
        elif discount >= 30:
            headline = "💥 DESCONTÃO"
        elif discount >= 10:
            headline = "🔥 SUPER OFERTA"
        else:
            headline = "🔥 PROMOÇÃO RELÂMPAGO"

        # Tag da loja
        store_tag = product.site.name if product.site else "Loja"

        # Constrói a mensagem em HTML (Telegram parse_mode=HTML)
        lines = []
        lines.append(f"<b>{headline}</b>")
        lines.append("")
        lines.append(MessageGenerator._escape(product.name))
        lines.append("")

        if product.original_price and product.original_price > product.current_price:
            lines.append(f"<s>De R$ {product.original_price:.2f}</s>")

        lines.append(f"<b>Por R$ {product.current_price:.2f}</b>")
        lines.append("🚚 Frete Grátis (verificar no checkout)")
        lines.append("")

        # Cupom
        if coupon:
            lines.append(f"🎟️ Utilize o cupom: <b>{MessageGenerator._escape(coupon.code)}</b>")
            if coupon.description:
                lines.append(f"<i>{MessageGenerator._escape(coupon.description)}</i>")
            lines.append("")

        # Tags
        if product.tags:
            tags = [t.strip() for t in product.tags.split(",") if t.strip()]
            tag_emojis = {
                "esportivo": "🏃",
                "casual": "👕",
                "preto": "⚫",
                "branco": "⚪",
                "dust": "🧢",
                "midas": "🧢",
                "soleil": "🧢",
                "mercado-livre": "🛒",
            }
            tag_strs = []
            for t in tags:
                emoji = tag_emojis.get(t, "🏷️")
                tag_strs.append(f"{emoji} {MessageGenerator._escape(t.title())}")
            if tag_strs:
                lines.append(" | ".join(tag_strs))
                lines.append("")

        # Loja
        lines.append(f"📍 {MessageGenerator._escape(store_tag)}")
        lines.append("")

        # Link
        link = product.url or ""
        if link and "mercadolivre" in link.lower() and AFFILIATE_CONFIG.get("mercadolivre"):
            link = link + ("&" if "?" in link else "?") + f"affiliate_tag={AFFILIATE_CONFIG['mercadolivre']}"

        safe_link = MessageGenerator._escape(link)
        lines.append(f'🛒 <b>Compre Aqui:</b> <a href="{safe_link}">Clique para comprar</a>')
        lines.append("")
        lines.append("⏳ Oferta por tempo limitado. Preços podem mudar sem aviso.")

        return {
            "text": "\n".join(lines),
            "image_url": product.image_url,
            "product_id": product.id,
            "coupon_code": coupon.code if coupon else None,
        }

    @staticmethod
    def generate_best_deals_summary(products: list[Product], limit: int = 5) -> str:
        """Gera um resumo dos melhores preços."""
        lines = ["📊 <b>TOP BONÉS ABA NENÊ - HOJE</b>", ""]

        sorted_products = sorted(
            [p for p in products if p.discount_percent],
            key=lambda x: x.discount_percent or 0,
            reverse=True
        )[:limit]

        for i, product in enumerate(sorted_products, 1):
            store = product.site.name if product.site else "Loja"
            discount = f" (-{product.discount_percent:.0f}%)" if product.discount_percent else ""
            lines.append(f"{i}. {MessageGenerator._escape(product.name)}")
            lines.append(f"   R$ {product.current_price:.2f}{discount} — {MessageGenerator._escape(store)}")
            lines.append("")

        return "\n".join(lines)


def create_promo_message(product_id: int, coupon_id: Optional[int] = None) -> Optional[dict]:
    """Cria uma mensagem de promoção e salva no banco."""
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        coupon = None
        if coupon_id:
            coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()

        gen = MessageGenerator()
        msg_data = gen.generate_product_message(product, coupon)

        from database import PromoMessage
        msg = PromoMessage(
            product_id=product_id,
            content=msg_data["text"],
            image_url=msg_data.get("image_url"),
            affiliate_link=product.url,
            coupon_code=msg_data.get("coupon_code"),
            status="draft",
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)

        msg_data["message_id"] = msg.id
        return msg_data
    finally:
        db.close()
