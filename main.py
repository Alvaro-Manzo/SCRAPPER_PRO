# -*- coding: utf-8 -*-
"""
Scraper Pro
====================
Herramienta avanzada para extracción de datos web con interfaz interactiva.

Autor: Alvaro Manzo
Versión: 2.0
Licencia: MIT
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import json
import csv
import logging
import sys
import os
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
import threading

try:
    from fake_useragent import UserAgent
    HAS_FAKE_USERAGENT = True
except ImportError:
    HAS_FAKE_USERAGENT = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MegaScraper")

class MegaScraper:
    """
    Clase principal del Web Scraper con funcionalidades avanzadas.
    """
    
    def __init__(self, use_proxies=False, delay=1.0, timeout=15, verify_ssl=True):
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.delay = delay
        self.use_proxies = use_proxies
        self.timeout = timeout
        self.proxies = []
        self.visited_urls = set()
        self.data = []
        self.lock = threading.Lock()
        
        # User agents predefinidos
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        # Configurar User Agent
        if HAS_FAKE_USERAGENT:
            try:
                self.ua = UserAgent()
                self.default_user_agent = self.ua.random
            except:
                self.default_user_agent = random.choice(self.user_agents)
        else:
            self.default_user_agent = random.choice(self.user_agents)
        
        self.session.headers.update({"User-Agent": self.default_user_agent})
        
        if self.use_proxies:
            self._load_proxies()

    def _load_proxies(self):
        """Carga proxies desde fuentes públicas."""
        try:
            sources = [
                'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
                'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt'
            ]
            
            for source in sources:
                try:
                    response = requests.get(source, timeout=5)
                    if response.status_code == 200:
                        found = [line.strip() for line in response.text.split('\n') 
                               if line.strip() and ':' in line][:50]  # Limitar a 50 proxies
                        self.proxies.extend(found)
                except:
                    continue
                    
            self.proxies = list(set(self.proxies))
            logger.info("[+] {} proxies cargados exitosamente".format(len(self.proxies)))
            
        except Exception as e:
            logger.error("[-] Error cargando proxies: {}".format(e))

    def _get_random_proxy(self):
        """Obtiene un proxy aleatorio."""
        if not self.proxies:
            return None
        proxy = random.choice(self.proxies)
        return {'http': 'http://' + proxy, 'https': 'http://' + proxy}

    def _rotate_headers(self):
        """Rota headers para evitar detección."""
        if HAS_FAKE_USERAGENT and hasattr(self, 'ua'):
            try:
                user_agent = self.ua.random
            except:
                user_agent = random.choice(self.user_agents)
        else:
            user_agent = random.choice(self.user_agents)
            
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.session.headers.update(headers)
        return headers

    def fetch_url(self, url, max_retries=3, method="GET", data=None, params=None, json_data=None):
        """Obtiene contenido de una URL con manejo de errores."""
        retries = 0
        while retries < max_retries:
            try:
                self._rotate_headers()
                proxy = self._get_random_proxy() if self.use_proxies else None

                if method.upper() == "GET":
                    response = self.session.get(url, timeout=self.timeout, proxies=proxy, params=params)
                elif method.upper() == "POST":
                    response = self.session.post(url, timeout=self.timeout, proxies=proxy, data=data, json=json_data)
                else:
                    response = self.session.request(method, url, timeout=self.timeout, proxies=proxy, 
                                                  data=data, json=json_data, params=params)

                response.raise_for_status()
                sleep_time = random.uniform(self.delay * 0.5, self.delay * 1.5)
                time.sleep(sleep_time)
                return response

            except requests.exceptions.RequestException as e:
                retries += 1
                logger.warning("[!] Error accediendo a {}: {}. Reintento {}/{}".format(
                    url, str(e)[:50], retries, max_retries))
                time.sleep(random.uniform(2, 5))

                if self.use_proxies and self.proxies and proxy and 'http' in proxy:
                    try:
                        proxy_addr = proxy['http'].replace('http://', '')
                        if proxy_addr in self.proxies:
                            self.proxies.remove(proxy_addr)
                    except:
                        pass

        logger.error("[-] No se pudo acceder a {} después de {} intentos".format(url, max_retries))
        return None

    def extract_data(self, url, selectors):
        """Extrae datos según selectores CSS proporcionados."""
        response = self.fetch_url(url)
        if not response:
            return None

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            data = {'url': url}

            for field, selector in selectors.items():
                try:
                    elements = soup.select(selector)
                    if not elements:
                        data[field] = None
                        continue

                    if len(elements) > 1:
                        data[field] = [el.get_text(strip=True) for el in elements[:10]]  # Limitar a 10
                    else:
                        data[field] = elements[0].get_text(strip=True)
                        
                except Exception as e:
                    logger.error("Error extrayendo {} con selector {}: {}".format(
                        field, selector, str(e)[:30]))
                    data[field] = None

            return data
            
        except Exception as e:
            logger.error("Error procesando {}: {}".format(url, str(e)[:50]))
            return None

    def extract_links(self, url, link_pattern=None):
        """Extrae enlaces de una página web."""
        response = self.fetch_url(url)
        if not response:
            return []

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            base_url = urlparse(url).scheme + '://' + urlparse(url).netloc
            links = []

            if link_pattern:
                elements = soup.select(link_pattern)
                for element in elements:
                    href = element.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        links.append(full_url)
            else:
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag.get('href')
                    if href:
                        full_url = urljoin(base_url, href)
                        links.append(full_url)

            # Filtrar enlaces internos únicos
            internal_links = []
            for link in links:
                if (urlparse(link).netloc == urlparse(url).netloc and 
                    link not in self.visited_urls and 
                    link not in internal_links):
                    internal_links.append(link)

            return internal_links[:200]  # Limitar a 200 enlaces
            
        except Exception as e:
            logger.error("Error extrayendo enlaces: {}".format(str(e)[:50]))
            return []

    def crawl_website(self, start_url, selectors, max_pages=10, depth=2, link_pattern=None):
        """Rastrea un sitio web recursivamente."""
        self.data = []
        self.visited_urls = set()
        urls_to_visit = [(start_url, 0)]

        print("[*] Iniciando crawling...")
        pages_processed = 0
        
        while urls_to_visit and pages_processed < max_pages:
            current_url, current_depth = urls_to_visit.pop(0)

            if current_url in self.visited_urls:
                continue

            self.visited_urls.add(current_url)
            pages_processed += 1
            
            print("[{}/{}] Procesando: {}".format(pages_processed, max_pages, current_url[:60] + "..."))
            logger.info("Visitando {} (profundidad {})".format(current_url, current_depth))

            item_data = self.extract_data(current_url, selectors)
            if item_data:
                self.data.append(item_data)

            if current_depth < depth:
                links = self.extract_links(current_url, link_pattern)
                for link in links:
                    if link not in self.visited_urls and len(urls_to_visit) < max_pages * 2:
                        urls_to_visit.append((link, current_depth + 1))

        print("[+] Crawling completado. {} páginas procesadas.".format(len(self.data)))

    def crawl_multiple_urls(self, urls, selectors, max_workers=5):
        """Extrae datos de múltiples URLs en paralelo."""
        self.data = []
        
        def worker(url):
            data = self.extract_data(url, selectors)
            if data:
                with self.lock:
                    self.data.append(data)
                    print("[+] Extraído: {}".format(url[:50] + "..."))

        print("[*] Procesando {} URLs en paralelo...".format(len(urls)))
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            executor.map(worker, urls)
            
        print("[+] Procesamiento completado. {} elementos extraídos.".format(len(self.data)))

    def save_to_csv(self, filename):
        """Guarda datos en formato CSV."""
        if not self.data:
            logger.warning("No hay datos para guardar en CSV")
            return

        try:
            if HAS_PANDAS:
                # Usar pandas si está disponible
                import pandas as pd
                df = pd.DataFrame(self.data)
                df.to_csv(filename, index=False, encoding='utf-8')
            else:
                # Usar csv estándar
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    if self.data:
                        fieldnames = self.data[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for row in self.data:
                            # Convertir listas a strings
                            clean_row = {}
                            for k, v in row.items():
                                if isinstance(v, list):
                                    clean_row[k] = '; '.join(str(x) for x in v)
                                else:
                                    clean_row[k] = str(v) if v is not None else ''
                            writer.writerow(clean_row)
                            
            logger.info("[+] Datos guardados en {}".format(filename))
            
        except Exception as e:
            logger.error("[-] Error guardando CSV: {}".format(e))

    def save_to_json(self, filename):
        """Guarda datos en formato JSON."""
        if not self.data:
            logger.warning("No hay datos para guardar en JSON")
            return

        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
            logger.info("[+] Datos guardados en {}".format(filename))
        except Exception as e:
            logger.error("[-] Error guardando JSON: {}".format(e))

    def extract_table(self, url, table_selector='table'):
        """Extrae tablas HTML de una página."""
        response = self.fetch_url(url)
        if not response:
            return None

        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            tables = soup.select(table_selector)

            if not tables:
                logger.warning("No se encontraron tablas con el selector {}".format(table_selector))
                return None

            all_tables = []
            for i, table in enumerate(tables):
                try:
                    if HAS_PANDAS:
                        # Usar pandas para leer tablas
                        df = pd.read_html(str(table))[0]
                        all_tables.append(df)
                    else:
                        # Extraer tabla manualmente
                        rows = []
                        for tr in table.find_all('tr'):
                            row = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                            if row:
                                rows.append(row)
                        all_tables.append(rows)
                except Exception as e:
                    logger.error("Error procesando tabla {}: {}".format(i, str(e)[:30]))
                    continue

            return all_tables
            
        except Exception as e:
            logger.error("Error extrayendo tablas: {}".format(str(e)[:50]))
            return None

# ============================================================================
# FUNCIONES DE INTERFAZ DE USUARIO
# ============================================================================

def print_banner():
    """Muestra el banner del programa con información útil."""
    print("=" * 80)
    print("           🚀 SCRAPPER 🚀")
    print("=" * 80)
    print("🌐 Herramienta avanzada para extracción de datos web")
    print("")
    print("📋 ¿Qué puedes hacer con este scraper?")
    print("   • Extraer datos de cualquier sitio web")
    print("   • Obtener precios, títulos, descripciones automáticamente")
    print("   • Explorar sitios completos siguiendo enlaces")
    print("   • Procesar múltiples URLs al mismo tiempo")
    print("   • Convertir tablas HTML a archivos Excel")
    print("   • Recopilar listas de enlaces")
    print("")
    print("✨ Características técnicas:")
    print("   • Rotación automática de User-Agents (evita bloqueos)")
    print("   • Soporte para proxies (mayor anonimato)")
    print("   • Procesamiento paralelo (más velocidad)")
    print("   • Exportación a CSV y JSON")
    print("=" * 80)

def mostrar_menu():
    """Muestra el menú principal con explicaciones detalladas."""
    print("\n" + "=" * 80)
    print("                    📋 MENÚ PRINCIPAL")
    print("=" * 80)
    print("")
    print("¿Qué tipo de extracción quieres realizar?")
    print("")
    print("1️⃣  EXTRACCIÓN SIMPLE")
    print("    └ Ideal para: Una sola página web")
    print("    └ Ejemplo: Extraer precio de un producto específico")
    print("    └ Uso: Rápido y directo")
    print("")
    print("2️⃣  EXPLORADOR WEB (CRAWLING)")
    print("    └ Ideal para: Sitios completos (tiendas, blogs, catálogos)")
    print("    └ Ejemplo: Obtener todos los productos de una tienda online")
    print("    └ Uso: Automático, sigue enlaces internos")
    print("")
    print("3️⃣  EXTRACCIÓN MÚLTIPLE")
    print("    └ Ideal para: Lista de URLs que ya tienes")
    print("    └ Ejemplo: Comparar precios de un producto en varias tiendas")
    print("    └ Uso: Procesa muchas URLs en paralelo")
    print("")
    print("4️⃣  EXTRACTOR DE TABLAS")
    print("    └ Ideal para: Datos estructurados (tablas HTML)")
    print("    └ Ejemplo: Extraer tabla de resultados, estadísticas")
    print("    └ Uso: Convierte automáticamente a Excel/CSV")
    print("")
    print("5️⃣  RECOLECTOR DE ENLACES")
    print("    └ Ideal para: Obtener todas las URLs de una página")
    print("    └ Ejemplo: Encontrar todos los productos de una categoría")
    print("    └ Uso: Lista completa de enlaces para usar después")
    print("")
    print("0️⃣  SALIR")
    print("    └ Terminar el programa")
    print("")
    print("=" * 80)

def get_user_input():
    """Obtiene configuración del usuario con explicaciones paso a paso."""
    print("\n" + "🔧" * 20 + " CONFIGURACIÓN DEL SCRAPER " + "🔧" * 20)
    print("")
    print("Vamos a configurar tu scraper paso a paso...")
    print("")
    
    # Configuración de proxies
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔐 CONFIGURACIÓN DE PROXIES")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("💡 ¿Qué son los proxies?")
    print("   Los proxies ocultan tu dirección IP real, útil para:")
    print("   ✓ Evitar ser bloqueado por el sitio web")
    print("   ✓ Acceder a contenido restringido geográficamente")
    print("   ✓ Realizar scraping más sigiloso")
    print("")
    print("⚠️  NOTA: Los proxies pueden ser más lentos")
    print("")
    use_proxies = input("¿Quieres usar proxies? (s/n) [Recomendado para sitios grandes]: ").lower().startswith('s')
    
    # Configuración de delay
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("⏱️  VELOCIDAD DE EXTRACCIÓN")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("💡 ¿Qué es el delay?")
    print("   Tiempo de espera entre cada petición al servidor:")
    print("   • 0.5 segundos = MUY RÁPIDO (riesgo de bloqueo)")
    print("   • 1.0 segundos = RECOMENDADO (equilibrio perfecto)")
    print("   • 2.0 segundos = CONSERVADOR (muy seguro pero lento)")
    print("   • 5.0+ segundos = ULTRA SEGURO (para sitios muy estrictos)")
    print("")
    delay_input = input("Delay entre requests en segundos [1.0]: ").strip()
    delay = float(delay_input) if delay_input else 1.0
    
    # Configuración de timeout
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("⏰ TIEMPO LÍMITE DE ESPERA")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("💡 ¿Qué es el timeout?")
    print("   Tiempo máximo para esperar respuesta del servidor:")
    print("   • 10 segundos = Conexiones rápidas")
    print("   • 15 segundos = RECOMENDADO (estándar)")
    print("   • 30 segundos = Conexiones lentas")
    print("")
    timeout_input = input("Timeout por request en segundos [15]: ").strip()
    timeout = int(timeout_input) if timeout_input else 15

    # Mostrar menú de opciones
    mostrar_menu()
    
    choice = input("👉 Selecciona una opción (1-5, 0 para salir): ").strip()

    return {
        'use_proxies': use_proxies,
        'delay': delay,
        'timeout': timeout,
        'choice': choice
    }

def configure_selectors():
    """Configura selectores CSS para extracción con tutorial interactivo."""
    print("\n" + "🎯" * 15 + " CONFIGURACIÓN DE SELECTORES CSS " + "🎯" * 15)
    print("")
    print("📚 TUTORIAL RÁPIDO DE SELECTORES CSS:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("🔍 ¿Qué son los selectores CSS?")
    print("   Son 'direcciones' que le dicen al scraper EXACTAMENTE qué extraer")
    print("")
    print("📝 EJEMPLOS COMUNES:")
    print("")
    print("   🏷️  Para TÍTULOS:")
    print("       h1                    → Primer título de la página")
    print("       .title                → Elementos con clase 'title'")
    print("       #main-title           → Elemento con ID 'main-title'")
    print("       .product-name         → Nombres de productos")
    print("")
    print("   💰 Para PRECIOS:")
    print("       .price                → Elementos con clase 'price'")
    print("       .cost                 → Elementos con clase 'cost'")
    print("       span.price-value      → Span con clase 'price-value'")
    print("       .product-price        → Precios de productos")
    print("")
    print("   📖 Para DESCRIPCIONES:")
    print("       .description          → Descripciones generales")
    print("       p                     → Todos los párrafos")
    print("       .summary              → Resúmenes")
    print("       .product-details      → Detalles de productos")
    print("")
    print("   🔗 Para ENLACES:")
    print("       a                     → Todos los enlaces")
    print("       .link                 → Enlaces con clase específica")
    print("")
    print("   🖼️  Para IMÁGENES:")
    print("       img                   → Todas las imágenes")
    print("       .product-image        → Imágenes de productos")
    print("")
    print("💡 CONSEJO PRO:")
    print("   1. Ve al sitio web en tu navegador")
    print("   2. Presiona F12 para abrir DevTools")
    print("   3. Haz clic derecho en el elemento que quieres → 'Inspeccionar'")
    print("   4. Busca class='algo' o id='algo' en el código HTML")
    print("   5. Usa .algo para clases o #algo para IDs")
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    print("🎯 Ahora vamos a configurar TUS selectores:")
    print("   (Deja un campo vacío y presiona Enter para terminar)")
    print("")

    selectors = {}
    ejemplos = [
        ("titulo", "h1, .title, .product-name"),
        ("precio", ".price, .cost, .price-value"),
        ("descripcion", ".description, p, .summary"),
        ("imagen", "img, .product-image"),
        ("enlace", "a")
    ]
    
    contador = 1
    while True:
        if contador <= len(ejemplos):
            sugerencia = ejemplos[contador-1]
            field_name = input("{}. Nombre del campo [Sugerencia: '{}']: ".format(contador, sugerencia[0])).strip()
            if not field_name:
                field_name = sugerencia[0]
        else:
            field_name = input("{}. Nombre del campo (ej: categoria, marca, etc.): ".format(contador)).strip()
            
        if not field_name:
            break

        if contador <= len(ejemplos) and field_name == ejemplos[contador-1][0]:
            print("   💡 Sugerencia para '{}': {}".format(field_name, ejemplos[contador-1][1]))
            
        selector = input("   🎯 Selector CSS para '{}': ".format(field_name)).strip()
        if selector:
            selectors[field_name] = selector
            print("   ✅ Guardado: {} → {}".format(field_name, selector))
        else:
            print("   ⚠️  Selector vacío, saltando...")
            
        contador += 1
        print("")

    if selectors:
        print("🎉 CONFIGURACIÓN COMPLETADA:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        for i, (campo, selector) in enumerate(selectors.items(), 1):
            print("   {}. {}: {}".format(i, campo, selector))
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    else:
        print("⚠️  No se configuraron selectores")

    return selectors

def show_sample_data(data, max_items=3):
    """Muestra datos de ejemplo."""
    if not data:
        return
        
    print("\n>>> MUESTRA DE DATOS EXTRAÍDOS:")
    for i, item in enumerate(data[:max_items], 1):
        print("\n--- Elemento {} ---".format(i))
        for key, value in item.items():
            if isinstance(value, list):
                display_value = value[:2] if len(value) > 2 else value
                if len(value) > 2:
                    display_value.append("... y {} más".format(len(value) - 2))
                print("  {}: {}".format(key, display_value))
            else:
                display_value = str(value)[:100]
                if len(str(value)) > 100:
                    display_value += "..."
                print("  {}: {}".format(key, display_value))
    
    if len(data) > max_items:
        print("\n... y {} elementos más".format(len(data) - max_items))

def save_data(scraper, data_name="datos"):
    """Interfaz para guardar datos."""
    if not scraper.data:
        print("[-] No hay datos para guardar")
        return
        
    print("\n>>> OPCIONES DE GUARDADO")
    save_csv = input("¿Guardar en CSV? (s/n): ").lower().startswith('s')
    save_json = input("¿Guardar en JSON? (s/n): ").lower().startswith('s')
    
    if save_csv or save_json:
        filename = input("Nombre del archivo (sin extensión): ").strip() or data_name
        
        if save_csv:
            scraper.save_to_csv("{}.csv".format(filename))
        if save_json:
            scraper.save_to_json("{}.json".format(filename))

def main():
    """Función principal del programa con interfaz mejorada."""
    print_banner()
    
    print("\n" + "🎉" * 20)
    print("¡Bienvenido al Scraper más potente y fácil de usar!")
    print("🎉" * 20)
    print("")
    print("📖 ANTES DE EMPEZAR:")
    print("   • Este programa es 100% legal para uso educativo y personal")
    print("   • Respeta los robots.txt y términos de servicio de los sitios")
    print("   • Usa delays apropiados para no sobrecargar servidores")
    print("   • Algunos sitios requieren registro/login previo")
    print("")
    
    continuar = input("¿Estás listo para empezar? (s/n): ").lower().startswith('s')
    if not continuar:
        print("👋 ¡Hasta la próxima!")
        return

    try:
        while True:  # Bucle principal para múltiples operaciones
            config = get_user_input()
            
            # Opción de salir
            if config['choice'] == '0':
                print("\n👋 ¡Gracias por usar el Scraper!")
                print("🌟 Si te sirvió, compártelo con tus amigos desarrolladores!")
                break

            # Inicializar scraper
            print("\n" + "🚀" * 20 + " INICIANDO SCRAPER " + "🚀" * 20)
            print("⚙️  Configurando scraper...")
            if config['use_proxies']:
                print("🔐 Cargando proxies...")
            print("🔄 Configurando rotación de User-Agents...")
            
            scraper = MegaScraper(
                use_proxies=config['use_proxies'],
                delay=config['delay'],
                timeout=config['timeout']
            )
            print("✅ Scraper configurado correctamente!")

            # Opción 1: Extraer datos de una sola URL
            if config['choice'] == '1':
                print("\n" + "🎯" * 15 + " EXTRACCIÓN SIMPLE " + "🎯" * 15)
                print("")
                print("📋 Vas a extraer datos de UNA SOLA página web")
                print("💡 Perfecto para obtener información específica rápidamente")
                print("")
                
                url = input("🌐 URL a scrapear: ").strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                    print("🔧 URL corregida: {}".format(url))
                    
                if not url:
                    print("❌ URL no válida")
                    continue
                    
                selectors = configure_selectors()

                if selectors:
                    print("\n🔍 Extrayendo datos de {}...".format(url))
                    data = scraper.extract_data(url, selectors)
                    
                    if data:
                        scraper.data = [data]
                        print("\n✅ ¡Extracción exitosa!")
                        show_sample_data(scraper.data)
                        save_data(scraper, "extraccion_simple")
                    else:
                        print("❌ No se pudieron extraer datos")
                        print("💡 POSIBLES CAUSAS:")
                        print("   • Selectores CSS incorrectos")
                        print("   • La página requiere JavaScript")
                        print("   • El sitio bloquea bots")
                        print("   • Problemas de conexión")

            # Opción 2: Crawlear sitio web completo
            elif config['choice'] == '2':
                print("\n" + "🕷️" * 15 + " EXPLORADOR WEB " + "🕷️" * 15)
                print("")
                print("📋 Vas a explorar un sitio web COMPLETO")
                print("🤖 El scraper seguirá enlaces automáticamente")
                print("⚠️  CUIDADO: Puede ser muy lento en sitios grandes")
                print("")
                
                start_url = input("🌐 URL inicial para crawling: ").strip()
                if not start_url.startswith(('http://', 'https://')):
                    start_url = 'https://' + start_url
                    print("🔧 URL corregida: {}".format(start_url))
                    
                if not start_url:
                    print("❌ URL no válida")
                    continue
                    
                selectors = configure_selectors()
                if not selectors:
                    print("❌ Se necesitan selectores para el crawling")
                    continue
                
                print("\n⚙️  CONFIGURACIÓN AVANZADA:")
                print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                print("💡 Páginas: Cuántas páginas máximo quieres procesar")
                print("💡 Profundidad: Qué tan 'profundo' en el sitio quieres ir")
                print("   • Profundidad 1: Solo la página inicial")
                print("   • Profundidad 2: Página inicial + enlaces directos")
                print("   • Profundidad 3: Dos niveles más profundo")
                
                max_pages_input = input("📄 Máximo número de páginas [10]: ").strip()
                max_pages = int(max_pages_input) if max_pages_input else 10
                
                depth_input = input("🏗️  Profundidad máxima [2]: ").strip()
                depth = int(depth_input) if depth_input else 2
                
                print("🔗 Selector para enlaces (opcional):")
                print("   • Déjalo vacío para seguir TODOS los enlaces")
                print("   • Usa selectores específicos para filtrar")
                print("   • Ejemplo: a.product-link (solo enlaces de productos)")
                link_pattern = input("🎯 Selector de enlaces: ").strip() or None

                print("\n🕷️  Iniciando crawling...")
                print("⏳ Esto puede tomar varios minutos dependiendo del sitio...")
                scraper.crawl_website(start_url, selectors, max_pages, depth, link_pattern)

                if scraper.data:
                    print("\n🎉 ¡Crawling completado!")
                    print("📊 Se extrajeron datos de {} páginas".format(len(scraper.data)))
                    show_sample_data(scraper.data)
                    save_data(scraper, "crawl_completo")
                else:
                    print("❌ No se pudieron extraer datos durante el crawling")

            # Opción 3: Extraer de múltiples URLs
            elif config['choice'] == '3':
                print("\n" + "📋" * 15 + " EXTRACCIÓN MÚLTIPLE " + "📋" * 15)
                print("")
                print("📋 Vas a procesar MÚLTIPLES URLs al mismo tiempo")
                print("⚡ Procesamiento paralelo = MÁS VELOCIDAD")
                print("💡 Perfecto para comparar productos, precios, etc.")
                print("")
                
                print("🔗 ENTRADA DE URLs:")
                print("   • Ingresa una URL por línea")
                print("   • Presiona Enter vacío para terminar")
                print("   • Mínimo: 2 URLs, Recomendado: 5-50 URLs")
                print("")
                
                urls = []
                contador = 1
                while True:
                    url = input("{}. URL: ".format(contador)).strip()
                    if not url:
                        break
                    if not url.startswith(('http://', 'https://')):
                        url = 'https://' + url
                    urls.append(url)
                    contador += 1

                if len(urls) < 2:
                    print("❌ Se necesitan al menos 2 URLs para extracción múltiple")
                    continue

                print("\n📊 URLs cargadas: {}".format(len(urls)))
                
                selectors = configure_selectors()
                if not selectors:
                    print("❌ Se necesitan selectores")
                    continue
                
                print("\n⚙️  CONFIGURACIÓN DE RENDIMIENTO:")
                print("💡 Hilos paralelos: Cuántas URLs procesar simultáneamente")
                print("   • 3-5 hilos: CONSERVADOR (sitios lentos)")
                print("   • 5-10 hilos: RECOMENDADO (equilibrio)")
                print("   • 10+ hilos: AGRESIVO (solo sitios rápidos)")
                    
                max_workers_input = input("🔥 Número de hilos paralelos [5]: ").strip()
                max_workers = int(max_workers_input) if max_workers_input else 5

                print("\n⚡ Procesando {} URLs con {} hilos...".format(len(urls), max_workers))
                scraper.crawl_multiple_urls(urls, selectors, max_workers)

                if scraper.data:
                    print("\n🎉 ¡Extracción múltiple completada!")
                    print("📊 Datos extraídos de {} URLs".format(len(scraper.data)))
                    show_sample_data(scraper.data)
                    save_data(scraper, "extraccion_multiple")

            # Opción 4: Extraer tablas
            elif config['choice'] == '4':
                print("\n" + "📊" * 15 + " EXTRACTOR DE TABLAS " + "📊" * 15)
                print("")
                print("📊 Vas a extraer TABLAS HTML y convertirlas a Excel/CSV")
                print("💡 Perfecto para estadísticas, resultados, precios, etc.")
                print("🎯 Busca automáticamente todas las tablas en la página")
                print("")
                
                url = input("🌐 URL con tablas: ").strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                    print("🔧 URL corregida: {}".format(url))
                    
                if not url:
                    print("❌ URL no válida")
                    continue
                
                print("\n🎯 SELECTOR DE TABLAS:")
                print("💡 Normalmente 'table' funciona para todas las tablas")
                print("💡 Usa selectores específicos para filtrar:")
                print("   • table.datos → Solo tablas con clase 'datos'")
                print("   • #tabla1 → Solo la tabla con ID 'tabla1'")
                print("   • .price-table → Solo tablas de precios")
                    
                table_selector = input("📋 Selector CSS para tablas [table]: ").strip() or "table"

                print("\n📊 Extrayendo tablas de {}...".format(url))
                tables = scraper.extract_table(url, table_selector)

                if tables:
                    print("\n🎉 ¡Se encontraron {} tablas!".format(len(tables)))

                    for i, table in enumerate(tables):
                        print("\n" + "━" * 50)
                        print("📊 TABLA {} de {}".format(i + 1, len(tables)))
                        print("━" * 50)
                        
                        if HAS_PANDAS and hasattr(table, 'head'):
                            print("📏 Dimensiones: {} filas x {} columnas".format(len(table), len(table.columns)))
                            print("\n🔍 VISTA PREVIA:")
                            print(table.head())
                            
                            save_table = input("\n💾 ¿Guardar tabla {} en CSV? (s/n): ".format(i + 1)).lower().startswith('s')
                            if save_table:
                                filename = input("📁 Nombre del archivo [tabla_{}]: ".format(i + 1)).strip() or "tabla_{}".format(i + 1)
                                table.to_csv("{}.csv".format(filename), index=False, encoding='utf-8')
                                print("✅ Tabla guardada como {}.csv".format(filename))
                        else:
                            print("📏 Filas encontradas: {}".format(len(table)))
                            print("\n🔍 VISTA PREVIA (primeras 5 filas):")
                            for j, row in enumerate(table[:5]):
                                print("  {}: {}".format(j + 1, row))
                            if len(table) > 5:
                                print("  ... y {} filas más".format(len(table) - 5))
                                
                            save_table = input("\n💾 ¿Guardar tabla {} en CSV? (s/n): ".format(i + 1)).lower().startswith('s')
                            if save_table:
                                filename = input("📁 Nombre del archivo [tabla_{}]: ".format(i + 1)).strip() or "tabla_{}".format(i + 1)
                                with open("{}.csv".format(filename), 'w', newline='', encoding='utf-8') as f:
                                    writer = csv.writer(f)
                                    writer.writerows(table)
                                print("✅ Tabla guardada como {}.csv".format(filename))
                else:
                    print("❌ No se encontraron tablas")
                    print("💡 POSIBLES CAUSAS:")
                    print("   • No hay tablas en la página")
                    print("   • Selector CSS incorrecto")
                    print("   • Las tablas se cargan con JavaScript")

            # Opción 5: Extraer enlaces
            elif config['choice'] == '5':
                print("\n" + "🔗" * 15 + " RECOLECTOR DE ENLACES " + "🔗" * 15)
                print("")
                print("🔗 Vas a extraer TODOS los enlaces de una página")
                print("💡 Útil para encontrar productos, artículos, categorías, etc.")
                print("📋 Genera lista completa para usar en extracción múltiple")
                print("")
                
                url = input("🌐 URL para extraer enlaces: ").strip()
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                    print("🔧 URL corregida: {}".format(url))
                    
                if not url:
                    print("❌ URL no válida")
                    continue
                
                print("\n🎯 FILTRO DE ENLACES:")
                print("💡 Déjalo vacío para extraer TODOS los enlaces")
                print("💡 Usa selectores para filtrar enlaces específicos:")
                print("   • a.product → Solo enlaces de productos")
                print("   • a[href*='categoria'] → Enlaces que contengan 'categoria'")
                print("   • .menu a → Solo enlaces del menú")
                    
                link_pattern = input("🔗 Selector CSS para enlaces: ").strip() or None

                print("\n🔍 Extrayendo enlaces de {}...".format(url))
                links = scraper.extract_links(url, link_pattern)

                if links:
                    print("\n🎉 ¡Se encontraron {} enlaces!".format(len(links)))
                    
                    # Mostrar muestra de enlaces
                    print("\n🔍 MUESTRA DE ENLACES:")
                    print("━" * 80)
                    for i, link in enumerate(links[:20], 1):
                        print("  {}. {}".format(i, link))

                    if len(links) > 20:
                        print("  ... y {} enlaces más".format(len(links) - 20))

                    save_links = input("\n💾 ¿Guardar enlaces en archivo de texto? (s/n): ").lower().startswith('s')
                    if save_links:
                        filename = input("📁 Nombre del archivo [enlaces]: ").strip() or "enlaces"
                        with open("{}.txt".format(filename), 'w', encoding='utf-8') as f:
                            for link in links:
                                f.write("{}\n".format(link))
                        print("✅ {} enlaces guardados en {}.txt".format(len(links), filename))
                        print("💡 Puedes usar este archivo para extracción múltiple!")
                else:
                    print("❌ No se encontraron enlaces")
                    print("💡 POSIBLES CAUSAS:")
                    print("   • Selector CSS muy restrictivo")
                    print("   • La página no tiene enlaces")
                    print("   • Los enlaces se cargan con JavaScript")

            else:
                print("\n❌ Opción no válida")
                continue
            
            # Preguntar si quiere hacer otra operación
            print("\n" + "🔄" * 20)
            otra_operacion = input("¿Quieres realizar otra extracción? (s/n): ").lower().startswith('s')
            if not otra_operacion:
                print("\n👋 ¡Gracias por usar el scrapper!")
                print("⭐ Si te gustó, ¡compártelo con otros desarrolladores!")
                break

    except KeyboardInterrupt:
        print("\n🛑 Operación cancelada por el usuario")
        print("👋 ¡Hasta la próxima!")
    except Exception as e:
        print("\n💥 Error inesperado: {}".format(e))
        print("🐛 Si el error persiste, reporta el problema")
        logger.error("Error en main: {}".format(e))

if __name__ == "__main__":
    main()