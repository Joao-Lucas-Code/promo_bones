"""Configurações do projeto Promo Bonés."""
import os

try:
    from dotenv import load_dotenv  # type: ignore[import-not-found]
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Carrega variáveis do .env
load_dotenv()

# === DATABASE ===
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./promo_bones.db")

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_GROUP_ID = os.getenv("TELEGRAM_GROUP_ID", "")  # ID do grupo/canal para envio

# === SITES CONFIG ===
SITES = {
    "thedustcompany": {
        "name": "The Dust Company",
        "base_url": "https://www.thedustcompany.com.br",
        "category_url": "/categoria/bones/",
        "enabled": True,
    },
    "midastouch": {
        "name": "Midas Touch",
        "base_url": "https://midastouch.com.br",
        "category_url": "/bones/",
        "enabled": True,
    },
    "soleilpassionnes": {
        "name": "Soleil Passionnés",
        "base_url": "https://soleilpassionnes.com",
        "category_url": "/collections/shop-all?filter.p.t.category=ae-2-2-10-1-2&sort_by=manual",
        "enabled": True,
    },
    "mercadolivre": {
        "name": "Mercado Livre",
        "base_url": "https://lista.mercadolivre.com.br",
        # URL de fallback para scraping HTML (usada caso a API pública seja bloqueada)
        "search_url": "/bon%C3%A9-aba-curva",
        # Configurações da API pública do Mercado Livre
        "api_query": "boné aba curva",
        # "seller_nickname": "THE-DUST-COMPANY",  # descomente para filtrar por loja específica
        "enabled": True,
    },
}

# === SCRAPER ===
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15

# === AFFILIATE ===
# Configuração de links de afiliado (deixe vazio para link direto)
AFFILIATE_CONFIG = {
    "mercadolivre": os.getenv("ML_AFFILIATE_TAG", ""),
    "amazon": os.getenv("AMAZON_AFFILIATE_TAG", ""),
}

# === SCHEDULER ===
SCRAPER_INTERVAL_MINUTES = int(os.getenv("SCRAPER_INTERVAL", "60"))

# === APP ===
APP_TITLE = "Promo Bonés - Painel Admin"
APP_VERSION = "1.0.0"

# === ADMIN AUTH ===
# Configure usuário e senha forte via variáveis de ambiente.
# Deixe ADMIN_USERNAME vazio para desabilitar a autenticação (apenas desenvolvimento local).
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
