"""Database models and connection for Promo Bonés."""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean,
    DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from .config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Site(Base):
    """Lojas/sites monitorados."""
    __tablename__ = "sites"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String)
    base_url = Column(String)
    category_url = Column(String, nullable=True)
    search_url = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="site", cascade="all, delete-orphan")


class Product(Base):
    """Produtos (bonés) rastreados."""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"))
    name = Column(String)
    url = Column(Text)
    image_url = Column(Text, nullable=True)
    original_price = Column(Float, nullable=True)
    current_price = Column(Float)
    discount_percent = Column(Float, nullable=True)
    currency = Column(String, default="BRL")
    available = Column(Boolean, default=True)
    sku = Column(String, nullable=True)
    tags = Column(Text, nullable=True)  # ex: "esportivo,aba-nene,preto"
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    site = relationship("Site", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    messages = relationship("PromoMessage", back_populates="product")


class PriceHistory(Base):
    """Histórico de preços."""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="price_history")


class Coupon(Base):
    """Cupons ativos."""
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    code = Column(String)
    description = Column(Text, nullable=True)
    discount_value = Column(Float, nullable=True)
    discount_type = Column(String, default="percent")  # percent ou fixed
    min_purchase = Column(Float, nullable=True)
    max_discount = Column(Float, nullable=True)
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    auto_applied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PromoMessage(Base):
    """Mensagens de promoção geradas e enviadas."""
    __tablename__ = "promo_messages"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    content = Column(Text)
    image_url = Column(Text, nullable=True)
    affiliate_link = Column(Text, nullable=True)
    coupon_code = Column(String, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    telegram_message_id = Column(Integer, nullable=True)
    status = Column(String, default="draft")  # draft, queued, sent, error
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="messages")


class ScraperLog(Base):
    """Logs de execução do scraper."""
    __tablename__ = "scraper_logs"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("sites.id"), nullable=True)
    status = Column(String)  # running, success, error
    products_found = Column(Integer, default=0)
    products_new = Column(Integer, default=0)
    products_updated = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


def init_db():
    """Cria todas as tabelas."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Gerador de sessão DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
