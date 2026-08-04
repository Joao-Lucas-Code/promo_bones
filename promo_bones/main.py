"""Flask app - Painel Admin Promo Bonés."""
import asyncio
import os
import requests as req
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from sqlalchemy.orm import Session

from config import APP_TITLE, APP_VERSION, SITES, SCRAPER_INTERVAL_MINUTES
from database import init_db, get_db, Site, Product, Coupon, PromoMessage, ScraperLog
from scraper import run_scraper, run_all_scrapers
from message_generator import create_promo_message, MessageGenerator
from telegram_bot import send_promo_message_sync, check_bot_config_sync

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = os.getenv("FLASK_SECRET_KEY", "promo-bones-secret-key-change-later")

# Helper to get DB session per request
def get_db_session():
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()

# === INIT ===
@app.before_request
def before_first():
    init_db()
    # Seed sites on first run
    db = next(get_db())
    try:
        for slug, cfg in SITES.items():
            site = db.query(Site).filter(Site.slug == slug).first()
            if not site:
                site = Site(
                    slug=slug,
                    name=cfg["name"],
                    base_url=cfg["base_url"],
                    category_url=cfg.get("category_url"),
                    search_url=cfg.get("search_url"),
                    enabled=cfg.get("enabled", True),
                )
                db.add(site)
        db.commit()
    finally:
        db.close()

# === DASHBOARD ===
@app.route("/")
def dashboard():
    db = next(get_db())
    try:
        total_products = db.query(Product).count()
        total_coupons = db.query(Coupon).filter(Coupon.is_active == True).count()
        total_messages = db.query(PromoMessage).count()
        sent_messages = db.query(PromoMessage).filter(PromoMessage.status == "sent").count()
        latest_logs = db.query(ScraperLog).order_by(ScraperLog.started_at.desc()).limit(5).all()
        best_deals = db.query(Product).filter(Product.discount_percent != None).order_by(Product.discount_percent.desc()).limit(5).all()

        bot_status = check_bot_config_sync()

        return render_template("dashboard.html",
            title=APP_TITLE,
            version=APP_VERSION,
            stats={
                "products": total_products,
                "coupons": total_coupons,
                "messages": total_messages,
                "sent": sent_messages,
            },
            latest_logs=latest_logs,
            best_deals=best_deals,
            bot_status=bot_status,
            scraper_interval=SCRAPER_INTERVAL_MINUTES,
        )
    finally:
        db.close()

# === SITES ===
@app.route("/sites")
def sites_list():
    db = next(get_db())
    try:
        sites = db.query(Site).all()
        return render_template("sites.html", sites=sites)
    finally:
        db.close()

@app.route("/sites/add", methods=["POST"])
def add_site():
    db = next(get_db())
    try:
        slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
        name = request.form.get("name", "").strip()
        base_url = request.form.get("base_url", "").strip()
        category_url = request.form.get("category_url", "").strip() or None
        search_url = request.form.get("search_url", "").strip() or None

        if not slug or not name or not base_url:
            return "Slug, nome e URL base são obrigatórios", 400

        existing = db.query(Site).filter(Site.slug == slug).first()
        if existing:
            return "Já existe um site com esse slug", 400

        site = Site(
            slug=slug,
            name=name,
            base_url=base_url,
            category_url=category_url,
            search_url=search_url,
            enabled=True,
        )
        db.add(site)
        db.commit()
        return redirect("/sites")
    finally:
        db.close()

@app.route("/sites/<int:site_id>/delete", methods=["POST"])
def delete_site(site_id):
    db = next(get_db())
    try:
        site = db.query(Site).filter(Site.id == site_id).first()
        if site:
            db.delete(site)
            db.commit()
        return redirect("/sites")
    finally:
        db.close()

@app.route("/sites/<int:site_id>/toggle", methods=["POST"])
def toggle_site(site_id):
    db = next(get_db())
    try:
        site = db.query(Site).filter(Site.id == site_id).first()
        if not site:
            return jsonify({"success": False, "error": "Site não encontrado"}), 404
        site.enabled = not site.enabled
        db.commit()
        return jsonify({"success": True, "enabled": site.enabled})
    finally:
        db.close()

# === PRODUCTS ===
@app.route("/products")
def products_list():
    db = next(get_db())
    try:
        search = request.args.get("search")
        site_id = request.args.get("site_id", type=int)
        min_discount = request.args.get("min_discount", type=float)

        query = db.query(Product).join(Site)
        if search:
            query = query.filter(Product.name.ilike(f"%{search}%"))
        if site_id:
            query = query.filter(Product.site_id == site_id)
        if min_discount:
            query = query.filter(Product.discount_percent >= min_discount)

        products = query.order_by(Product.updated_at.desc()).limit(100).all()
        sites = db.query(Site).all()

        return render_template("products.html",
            products=products,
            sites=sites,
            search=search,
            site_id=site_id,
            min_discount=min_discount,
        )
    finally:
        db.close()

# === COUPONS ===
@app.route("/coupons")
def coupons_list():
    db = next(get_db())
    try:
        coupons = db.query(Coupon).order_by(Coupon.created_at.desc()).all()
        sites = db.query(Site).all()
        return render_template("coupons.html", coupons=coupons, sites=sites)
    finally:
        db.close()

@app.route("/coupons/add", methods=["POST"])
def add_coupon():
    db = next(get_db())
    try:
        coupon = Coupon(
            code=request.form.get("code"),
            description=request.form.get("description"),
            site_id=request.form.get("site_id", type=int) or None,
            discount_value=request.form.get("discount_value", type=float) or None,
            discount_type=request.form.get("discount_type", "percent"),
            min_purchase=request.form.get("min_purchase", type=float) or None,
        )
        db.add(coupon)
        db.commit()
        return redirect("/coupons")
    finally:
        db.close()

@app.route("/coupons/<int:coupon_id>/toggle", methods=["POST"])
def toggle_coupon(coupon_id):
    db = next(get_db())
    try:
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if not coupon:
            return jsonify({"success": False, "error": "Cupom não encontrado"}), 404
        coupon.is_active = not coupon.is_active
        db.commit()
        return jsonify({"success": True, "is_active": coupon.is_active})
    finally:
        db.close()

@app.route("/coupons/<int:coupon_id>/delete", methods=["POST"])
def delete_coupon(coupon_id):
    db = next(get_db())
    try:
        coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
        if coupon:
            db.delete(coupon)
            db.commit()
        return redirect("/coupons")
    finally:
        db.close()

# === MESSAGES ===
@app.route("/messages")
def messages_list():
    db = next(get_db())
    try:
        messages = db.query(PromoMessage).order_by(PromoMessage.created_at.desc()).limit(50).all()
        products = db.query(Product).filter(Product.available == True).order_by(Product.discount_percent.desc().nullslast()).limit(50).all()
        coupons = db.query(Coupon).filter(Coupon.is_active == True).all()
        return render_template("messages.html", messages=messages, products=products, coupons=coupons)
    finally:
        db.close()

@app.route("/messages/generate", methods=["POST"])
def generate_message():
    product_id = request.form.get("product_id", type=int)
    coupon_id = request.form.get("coupon_id", type=int) or None
    result = create_promo_message(product_id, coupon_id)
    if not result:
        return "Erro ao gerar mensagem", 400
    return redirect("/messages")

@app.route("/messages/<int:message_id>/send", methods=["POST"])
def send_message_telegram(message_id):
    result = send_promo_message_sync(message_id)
    if result["success"]:
        return jsonify({"success": True, "telegram_message_id": result.get("telegram_message_id")})
    return jsonify({"success": False, "error": result.get("error", "Erro ao enviar")}), 400

@app.route("/messages/<int:message_id>/delete", methods=["POST"])
def delete_message(message_id):
    db = next(get_db())
    try:
        msg = db.query(PromoMessage).filter(PromoMessage.id == message_id).first()
        if msg:
            db.delete(msg)
            db.commit()
        return redirect("/messages")
    finally:
        db.close()

@app.route("/messages/<int:message_id>/preview")
def preview_message(message_id):
    db = next(get_db())
    try:
        msg = db.query(PromoMessage).filter(PromoMessage.id == message_id).first()
        if not msg:
            return jsonify({"error": "Mensagem não encontrada"}), 404
        return jsonify({"content": msg.content, "image_url": msg.image_url})
    finally:
        db.close()

# === SCRAPER ACTIONS ===
@app.route("/api/scraper/run/<site_slug>", methods=["POST"])
def api_run_scraper(site_slug):
    if site_slug == "all":
        results = run_all_scrapers()
        return jsonify({"success": True, "results": results})
    result = run_scraper(site_slug)
    return jsonify(result)

@app.route("/api/scraper/logs")
def api_scraper_logs():
    limit = request.args.get("limit", 10, type=int)
    db = next(get_db())
    try:
        logs = db.query(ScraperLog).order_by(ScraperLog.started_at.desc()).limit(limit).all()
        return jsonify([{"id": l.id, "site": l.site.name if l.site else None, "status": l.status,
                 "found": l.products_found, "new": l.products_new, "updated": l.products_updated,
                 "started": l.started_at.isoformat() if l.started_at else None} for l in logs])
    finally:
        db.close()

# === BOT ===
@app.route("/api/bot/status")
def api_bot_status():
    return jsonify(check_bot_config_sync())

@app.route("/api/bot/test-message", methods=["POST"])
def api_test_message():
    text = request.form.get("text", "🧢 Teste do bot Promo Bonés!")
    from telegram_bot import send_text_sync
    result = send_text_sync(text)
    return jsonify(result)

# === STATS ===
@app.route("/api/stats")
def api_stats():
    db = next(get_db())
    try:
        return jsonify({
            "products": db.query(Product).count(),
            "coupons_active": db.query(Coupon).filter(Coupon.is_active == True).count(),
            "messages_sent": db.query(PromoMessage).filter(PromoMessage.status == "sent").count(),
            "messages_draft": db.query(PromoMessage).filter(PromoMessage.status == "draft").count(),
        })
    finally:
        db.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
