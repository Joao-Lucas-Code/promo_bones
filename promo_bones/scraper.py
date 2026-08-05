"""Web scraper para sites de bonés."""
import os
import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .config import USER_AGENT, REQUEST_TIMEOUT, SITES
from .database import SessionLocal, Product, PriceHistory, Site, ScraperLog

# Tenta usar curl_cffi (melhor contra bloqueios de TLS/bot); fallback para requests
try:
    from curl_cffi import requests as curl_requests
    CURL_CFFI_AVAILABLE = True
except Exception:  # pragma: no cover
    import requests as curl_requests
    CURL_CFFI_AVAILABLE = False

import requests


PROXY_URL = os.getenv("SCRAPER_PROXY_URL", "")


HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}


class BaseScraper:
    """Classe base para scrapers."""

    def __init__(self, site_slug: str):
        self.site_slug = site_slug
        self.site_config = SITES.get(site_slug, {})
        self.last_response_text = ""
        self.last_url = ""
        self._build_session()

    def _build_session(self):
        """Monta a sessão HTTP, preferindo curl_cffi quando disponível."""
        proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
        if CURL_CFFI_AVAILABLE:
            self.session = curl_requests.Session()
            self.session.impersonate = "chrome131"
        else:
            self.session = requests.Session()
            self.session.headers.update(HEADERS)
        self.session.proxies = proxies

    def fetch(self, url: str) -> BeautifulSoup | None:
        try:
            if CURL_CFFI_AVAILABLE:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            else:
                resp = self.session.get(url, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            self.last_url = resp.url
            self.last_response_text = resp.text
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:
            print(f"[ERRO] Falha ao buscar {url}: {e}")
            return None

    def is_blocked(self) -> bool:
        """Detecta páginas de bloqueio/verificação do Mercado Livre."""
        text = self.last_response_text.lower()
        return any(marker in text for marker in [
            "suspicious-traffic",
            "account-verification",
            "micro-landing-container",
            "para continuar, acesse",
            "sua conta",
        ])

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
    """Scraper para Midas Touch (Nuvem Shop)."""

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        products = []
        # Nuvem Shop: .js-item-product ou .item-product
        items = soup.select(".js-item-product, .item-product")

        for item in items[:20]:
            name_el = item.select_one(".js-item-name, .item-name")
            price_el = item.select_one(".js-item-price, .item-price")
            old_price_el = item.select_one(".item-price-compare, .compare-price, .item-price-promotion")
            img_el = item.select_one(".js-item-image, .item-image img, img")
            link_el = item.select_one("a[href]")

            if not name_el or not price_el:
                continue

            name = name_el.get_text(strip=True)
            price = self._parse_price(price_el.get_text(strip=True))
            old_price = self._parse_price(old_price_el.get_text(strip=True)) if old_price_el else None

            discount = None
            if old_price and price and old_price > price:
                discount = round((old_price - price) / old_price * 100, 1)

            image = None
            if img_el:
                image = img_el.get("data-srcset") or img_el.get("srcset") or img_el.get("data-src") or img_el.get("src")
                # Pega a primeira URL do srcset
                if image:
                    image = image.split(",")[0].strip().split(" ")[0]
                if image and image.startswith("//"):
                    image = "https:" + image
                elif image and image.startswith("data:"):
                    image = None

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
                "tags": "aba-nene,midas",
            })

        return products

    def run(self) -> dict:
        url = self.site_config["base_url"] + self.site_config.get("category_url", "")
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}
        products = self.parse_products(soup)
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
    """Scraper para Mercado Livre.

    Tenta primeiro a API pública do Mercado Livre, que é mais estável e
    entrega preços originais/descontos de forma estruturada. Se a API for
    bloqueada (datacenter/cloud), faz fallback para scraping da página HTML.
    """

    API_BASE = "https://api.mercadolibre.com/sites/MLB/search"

    def _is_cap_hat(self, title: str) -> bool:
        """Filtra apenas bonés aba curva/nenê/dad hat/strapback."""
        name_lower = title.lower()
        keywords = ["boné", "bone", "aba curva", "dad hat", "strapback", "snapback"]
        return any(k in name_lower for k in keywords)

    def _parse_api_products(self, data: dict) -> list[dict]:
        products = []
        for item in data.get("results", [])[:20]:
            title = item.get("title", "").strip()
            if not title or not self._is_cap_hat(title):
                continue

            price = item.get("price")
            original_price = item.get("original_price")

            # Preço original pode estar nos atributos de preço
            if original_price is None and item.get("prices"):
                prices = item.get("prices", {}).get("prices", [])
                if prices:
                    # Pega o maior preço encontrado como referência
                    original_price = max(
                        (p.get("amount") for p in prices if p.get("amount")),
                        default=None,
                    )

            discount = None
            if original_price and price and original_price > price:
                discount = round((original_price - price) / original_price * 100, 1)

            products.append({
                "name": title,
                "current_price": price,
                "original_price": original_price,
                "discount_percent": discount,
                "image_url": item.get("thumbnail"),
                "url": item.get("permalink"),
                "sku": item.get("id"),
                "tags": "aba-nene,mercado-livre",
            })
        return products

    def _fetch_api(self) -> dict | None:
        """Busca produtos na API pública do Mercado Livre."""
        params = {
            "q": "boné aba curva",
            "sort": "price_asc",
            "limit": 50,
        }
        # Se houver seller configurado, filtra por loja oficial
        seller = self.site_config.get("seller_id") or self.site_config.get("seller_nickname")
        if seller:
            params["nickname"] = seller

        try:
            proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None
            resp = requests.get(
                self.API_BASE,
                params=params,
                headers=HEADERS,
                proxies=proxies,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"[ML API] Falha: {e}")
            return None

    def parse_products(self, soup: BeautifulSoup) -> list[dict]:
        products = []
        # Selectores usados nas listagens do ML (clássicos e novos "poly")
        items = soup.select(
            ".ui-search-result, .ui-search-layout__item, .poly-card, "
            ".andes-card--default, [data-testid='product-card']"
        )

        for item in items[:15]:
            name_el = item.select_one(
                ".poly-component__title, .ui-search-item__title, "
                ".ui-search-link__title-class, a[title]"
            )
            price_el = item.select_one(
                ".poly-price__current, .andes-money-amount__fraction, "
                ".price-tag-fraction, .ui-search-price__part"
            )
            old_price_el = item.select_one(
                ".poly-price__old, .andes-money-amount--previous, "
                ".price-tag-amount--previous, .ui-search-price__part--small"
            )
            img_el = item.select_one("img")
            link_el = item.select_one("a[href]")

            if not name_el:
                continue

            name = name_el.get_text(strip=True)
            price = self._parse_html_price(price_el.get_text(strip=True) if price_el else "")
            old_price = self._parse_html_price(old_price_el.get_text(strip=True) if old_price_el else "")

            discount = None
            if old_price and price and old_price > price:
                discount = round((old_price - price) / old_price * 100, 1)

            image = None
            if img_el:
                image = img_el.get("data-src") or img_el.get("src")

            link = link_el["href"] if link_el else None

            if self._is_cap_hat(name):
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
        # 1) Tenta API primeiro
        api_data = self._fetch_api()
        if api_data is not None:
            products = self._parse_api_products(api_data)
            if products:
                return {"success": True, "products": products, "error": None}
            # API respondeu, mas não achou bonés; não faz fallback para HTML
            return {
                "success": False,
                "products": [],
                "error": "API do Mercado Livre não retornou bonés com os filtros atuais.",
            }

        # 2) Fallback para HTML scraping
        print("[ML] API indisponível, tentando scraping HTML...")
        search_url = self.site_config.get("search_url", "")
        if "_OrderId" not in search_url:
            search_url += "_OrderId_PRICE_NoIndex_True"
        url = f"{self.site_config['base_url']}{search_url}"
        soup = self.fetch(url)
        if not soup:
            return {"success": False, "products": [], "error": "Falha ao carregar página"}

        if self.is_blocked():
            return {
                "success": False,
                "products": [],
                "error": (
                    "Mercado Livre bloqueou a requisição (verificação de conta / "
                    "tráfego suspeito). Considere usar SCRAPER_PROXY_URL ou cadastrar "
                    "o preço de referência do marketplace no painel."
                ),
            }

        products = self.parse_products(soup)
        if not products:
            return {
                "success": False,
                "products": [],
                "error": (
                    "Nenhum produto encontrado na listagem. O Mercado Livre pode estar "
                    "entregando uma página reduzida (JavaScript) ou a estrutura mudou."
                ),
            }
        return {"success": True, "products": products, "error": None}

    @staticmethod
    def _parse_html_price(text: str) -> float | None:
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
