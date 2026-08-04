"""Web scraper para sites de bonés."""
import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from config import USER_AGENT, REQUEST_TIMEOUT, SITES
from database import SessionLocal, Product, PriceHistory, Site, ScraperLog


HEADERS = {"User-Agent": USER_AGENT}


class BaseScraper:
    """Classe base para scrapers."""

    def __init__(self, site_slug: str):
        self.site_slug = site_slug
        self.site_config = SITES.get(site_slug, {})
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def fetch(self, url: str) -> BeautifulSoup | None:
        try:
            resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"[ERRO] Falha ao buscar {url}: {e}")
            return None

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        raise NotImplementedError

    def run(self) -> dict:
        raise NotImplementedError


class DustCompanyScraper(BaseScraper):
    """Scraper para The Dust Company."""

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        products = []
        # Selectores comuns de e-commerce Shopify/WooCommerce
        items = soup.select(".product-item, .grid__item, .product-card, .product")
        if not items:
            # Tenta selectores mais genéricos
            items = soup.find_all("div", class_=lambda c: c and ("product" in c.lower() or "item" in c.lower()))

        for item in items[:20]:
            name_el = item.select_one(".product-title, .product-name, h2, h3, a[title]")
            price_el = item.select_one(".price, .product-price, .money, .current-price")
            old_price_el = item.select_one(".compare-price, .old-price, .was-price")
            img_el = item.select_one("img")
            link_el = item.select_one("a[href]")

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price = self._parse_price(price_text)

            old_price = None
            if old_price_el:
                old_price = self._parse_price(old_price_el.get_text(strip=True))

            discount = None
            if old_price and price and old_price > price:
                discount = round((old_price - price) / old_price * 100, 1)

            image = None
            if img_el:
                image = img_el.get("data-src") or img_el.get("src")
                if image and image.startswith("//"):
                    image = "https:" + image

            link = None
            if link_el:
                link = urljoin(self.site_config["base_url"], link_el["href"])

            products.append({
                "name": name,
                "current_price": price,
                "original_price": old_price,
                "discount_percent": discount,
                "image_url": image,
                "url": link,
                "sku": None,
                "tags": "aba-nene,dust",
            })

        return products

    def run(self) -> dict:
        url = self.site_config["base_url"] + self.site_config.get("category_url", "")
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
        return {"success": True, "products": products, "error": None}

    @staticmethod
    def _parse_price(text: str) -> float | None:
        text = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        nums = re.findall(r"[\d.]+", text)
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
        return None


class MidasTouchScraper(DustCompanyScraper):
    """Scraper para Midas Touch (mesma estrutura)."""

    def run(self) -> dict:
        url = self.site_config["base_url"] + self.site_config.get("category_url", "")
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
        # Tag específica
        for p in products:
            p["tags"] = "aba-nene,midas"
        return {"success": True, "products": products, "error": None}


class SoleilScraper(DustCompanyScraper):
    """Scraper para Soleil Passionnés (Shopify)."""

    def run(self) -> dict:
        url = self.site_config["base_url"] + self.site_config.get("category_url", "")
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
        for p in products:
            p["tags"] = "aba-nene,soleil"
        return {"success": True, "products": products, "error": None}


class MercadoLivreScraper(BaseScraper):
    """Scraper para Mercado Livre."""

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        products = []
        items = soup.select(".ui-search-result, .ui-search-layout__item, .poly-card")

        for item in items[:15]:
            name_el = item.select_one(".poly-component__title, .ui-search-item__title")
            price_el = item.select_one(".poly-price__current, .andes-money-amount__fraction")
            old_price_el = item.select_one(".poly-price__old, .andes-money-amount--previous")
            img_el = item.select_one("img")
            link_el = item.select_one("a[href]")

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            price = self._parse_price(price_el.get_text(strip=True) if price_el else "")
            old_price = self._parse_price(old_price_el.get_text(strip=True) if old_price_el else "")

            discount = None
            if old_price and price and old_price > price:
                discount = round((old_price - price) / old_price * 100, 1)

            image = None
            if img_el:
                image = img_el.get("data-src") or img_el.get("src")

            link = link_el["href"] if link_el else None

            # Filtro: só bonés aba curva/nenê
            name_lower = name.lower()
            if any(k in name_lower for k in ["bone", "boné", "aba curva", "dad hat", "strapback"]):
                products.append({
                    "name": name,
                    "current_price": price,
                    "original_price": old_price,
                    "discount_percent": discount,
                    "image_url": image,
                    "url": link,
                    "sku": None,
                    "tags": "aba-nene,mercado-livre",
                })

        return products

    def run(self) -> dict:
        url = f"{self.site_config['base_url']}{self.site_config.get('search_url', '')}_OrderId_PRICE_NoIndex_True"
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
        return {"success": True, "products": products, "error": None}

    @staticmethod
    def _parse_price(text: str) -> float | None:
        text = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        nums = re.findall(r"[\d.]+", text)
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
        return None


class GenericScraper(BaseScraper):
    """Scraper genérico para sites adicionados pelo painel."""

    def __init__(self, site_slug: str, site_db=None):
        super().__init__(site_slug)
        self.site_db = site_db
        if site_db:
            self.site_config = {
                "base_url": site_db.base_url,
                "category_url": site_db.category_url or "",
                "search_url": site_db.search_url or "",
            }

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        products = []
        # Selectores comuns de e-commerce (Shopify, WooCommerce, etc.)
        items = soup.select(".product-item, .grid__item, .product-card, .product, .item")
        if not items:
            items = soup.find_all("div", class_=lambda c: c and ("product" in c.lower() or "item" in c.lower()))

        for item in items[:20]:
            name_el = item.select_one(".product-title, .product-name, h2, h3, a[title]")
            price_el = item.select_one(".price, .product-price, .money, .current-price")
            old_price_el = item.select_one(".compare-price, .old-price, .was-price")
            img_el = item.select_one("img")
            link_el = item.select_one("a[href]")

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price_text = price_el.get_text(strip=True)
            price = self._parse_price(price_text)

            old_price = None
            if old_price_el:
                old_price = self._parse_price(old_price_el.get_text(strip=True))

            discount = None
            if old_price and price and old_price > price:
                discount = round((old_price - price) / old_price * 100, 1)

            image = None
            if img_el:
                image = img_el.get("data-src") or img_el.get("src")
                if image and image.startswith("//"):
                    image = "https:" + image

            link = None
            if link_el:
                link = urljoin(self.site_config["base_url"], link_el["href"])

            products.append({
                "name": name,
                "current_price": price,
                "original_price": old_price,
                "discount_percent": discount,
                "image_url": image,
                "url": link,
                "sku": None,
                "tags": f"aba-nene,{self.site_slug}",
            })

        return products

    def run(self) -> dict:
        url = self.site_config["base_url"]
        if self.site_config.get("category_url"):
            url += self.site_config["category_url"]
        elif self.site_config.get("search_url"):
            url += self.site_config["search_url"]

        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
        return {"success": True, "products": products, "error": None}

    @staticmethod
    def _parse_price(text: str) -> float | None:
        text = text.replace("R$", "").replace(".", "").replace(",", ".").strip()
        nums = re.findall(r"[\d.]+", text)
        if nums:
            try:
                return float(nums[0])
            except ValueError:
                pass
        return None


SCRAPER_MAP = {
    "thedustcompany": DustCompanyScraper,
    "midastouch": MidasTouchScraper,
    "soleilpassionnes": SoleilScraper,
    "mercadolivre": MercadoLivreScraper,
}


def run_scraper(site_slug: str) -> dict:
    """Executa o scraper para um site específico."""
    db = SessionLocal()
    log = ScraperLog(site_id=None, status="running")
    db.add(log)
    db.commit()

    try:
        site = db.query(Site).filter(Site.slug == site_slug).first()
        if site:
            log.site_id = site.id
            db.commit()

        scraper_class = SCRAPER_MAP.get(site_slug)
        if scraper_class:
            scraper = scraper_class(site_slug)
        elif site:
            # Usa scraper genérico para sites adicionados pelo painel
            scraper = GenericScraper(site_slug, site_db=site)
        else:
            raise ValueError(f"Scraper não encontrado para: {site_slug}")

        result = scraper.run()

        if result["success"]:
            log.products_found = len(result["products"])
            log.products_new = 0
            log.products_updated = 0

            for data in result["products"]:
                if not data["current_price"]:
                    continue

                existing = db.query(Product).filter(
                    Product.name == data["name"],
                    Product.site_id == site.id if site else None
                ).first()

                if existing:
                    # Atualiza preço e histórico
                    if existing.current_price != data["current_price"]:
                        db.add(PriceHistory(product_id=existing.id, price=existing.current_price))
                        existing.current_price = data["current_price"]
                        existing.original_price = data.get("original_price")
                        existing.discount_percent = data.get("discount_percent")
                        log.products_updated += 1
                    existing.image_url = data.get("image_url") or existing.image_url
                    existing.url = data.get("url") or existing.url
                    existing.updated_at = datetime.utcnow()
                else:
                    # Novo produto
                    new_product = Product(
                        site_id=site.id if site else None,
                        name=data["name"],
                        url=data.get("url"),
                        image_url=data.get("image_url"),
                        original_price=data.get("original_price"),
                        current_price=data["current_price"],
                        discount_percent=data.get("discount_percent"),
                        tags=data.get("tags"),
                    )
                    db.add(new_product)
                    db.flush()
                    db.add(PriceHistory(product_id=new_product.id, price=data["current_price"]))
                    log.products_new += 1

            db.commit()
            log.status = "success"
        else:
            log.status = "error"
            log.error_message = result.get("error", "Erro desconhecido")

    except Exception as e:
        db.rollback()
        log.status = "error"
        log.error_message = str(e)
        result = {"success": False, "error": str(e), "products": []}
    finally:
        log.finished_at = datetime.utcnow()
        db.commit()
        db.close()

    return result


def run_all_scrapers() -> list[dict]:
    """Executa todos os scrapers habilitados do banco de dados."""
    db = SessionLocal()
    try:
        sites = db.query(Site).filter(Site.enabled == True).all()
        results = []
        for site in sites:
            print(f"[SCRAPER] Rodando {site.slug}...")
            result = run_scraper(site.slug)
            results.append({"site": site.slug, **result})
        return results
    finally:
        db.close()
