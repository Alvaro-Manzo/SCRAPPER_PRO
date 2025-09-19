# 🚀 Mega Web Scraper Pro

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Stable-brightgreen.svg)]()

Herramienta avanzada para extracción de datos web con interfaz interactiva en español. Diseñada para ser potente, fácil de usar y completamente personalizable.

## ✨ Características

- 🔄 **Rotación automática de User-Agents** - Evita detección
- 🛡️ **Soporte para proxies** - Múltiples fuentes de proxies públicos
- 🎯 **Selectores CSS personalizables** - Extrae exactamente lo que necesitas
- 🕷️ **Crawling recursivo** - Explora sitios web completos
- ⚡ **Procesamiento paralelo** - Múltiples URLs simultáneamente
- 📊 **Múltiples formatos de salida** - CSV, JSON, TXT
- 🔧 **Extracción de tablas HTML** - Convierte tablas a DataFrames
- � **Interfaz en español** - Fácil de usar para hispanohablantes
- 📝 **Logging detallado** - Seguimiento completo de operaciones

## � Instalación Rápida

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/mega-web-scraper.git
cd mega-web-scraper

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar el scraper
python main.py
```

## � Requisitos

- Python 3.7 o superior
- Conexión a internet
- Librerías especificadas en `requirements.txt`

### Dependencias principales:
- `requests` - Peticiones HTTP
- `beautifulsoup4` - Parsing HTML
- `pandas` - Manejo de datos (opcional)
- `fake-useragent` - Rotación de User-Agents (opcional)

## 🎯 Uso

### Ejecución básica
```bash
python main.py
```

### Opciones disponibles:

#### 1. **Extraer datos de una sola URL**
Perfecto para páginas individuales. Configura selectores CSS personalizados.

```
URL: https://ejemplo.com/producto
Selectores:
  - titulo: h1
  - precio: .price
  - descripcion: .description
```

#### 2. **Crawlear sitio web completo**
Explora automáticamente enlaces internos con control de profundidad.

```
URL inicial: https://blog.ejemplo.com
Páginas máximas: 50
Profundidad: 3
```

#### 3. **Extraer de múltiples URLs**
Procesa varias URLs en paralelo para máxima eficiencia.

```
URLs:
https://tienda.com/producto1
https://tienda.com/producto2
https://tienda.com/producto3
```

#### 4. **Extraer tablas HTML**
Encuentra y convierte tablas HTML a formato CSV.

#### 5. **Extraer enlaces**
Obtén todos los enlaces internos de una página.

## 🔧 Ejemplos de Selectores CSS

### E-commerce
```css
/* Nombre del producto */
h1.product-title

/* Precio */
.price, .product-price

/* Descripción */
.description, .product-description

/* Rating */
.rating-value, .stars
```

### Noticias
```css
/* Titular */
h1, .headline, .article-title

/* Autor */
.author, .byline

/* Fecha */
.date, .published-date

/* Contenido */
.article-content, .post-content
```

### Redes Sociales
```css
/* Posts */
.post, .tweet

/* Usuario */
.username, .user-handle

/* Texto */
.post-text, .tweet-text
```

## 📊 Formatos de Salida

### CSV
- Compatible con Excel y Google Sheets
- Codificación UTF-8
- Separación automática de listas

### JSON
- Estructura jerárquica preservada
- Fácil procesamiento programático
- Formato legible

### TXT
- Para listas de enlaces
- Una URL por línea
- Codificación UTF-8

## ⚙️ Configuración Avanzada

### Proxies
```python
# El scraper carga automáticamente proxies de fuentes públicas
use_proxies = True  # Activar en la configuración
```

### Delays y Timeouts
```python
delay = 2.0      # Segundos entre requests
timeout = 30     # Timeout por request
```

### Paralelización
```python
max_workers = 5  # Hilos simultáneos para múltiples URLs
```

## 🛡️ Uso Ético y Legal

### ✅ Buenas Prácticas
- Revisa `robots.txt` antes de hacer scraping
- Usa delays apropiados (1-3 segundos)
- No sobrecargues los servidores
- Respeta los términos de servicio
- Solo para uso educativo/personal

### ⚠️ Consideraciones
- Algunos sitios pueden bloquear bots
- El scraping intensivo puede afectar el rendimiento del sitio
- Siempre verifica la legalidad en tu jurisdicción

## 📁 Estructura del Proyecto

```
mega-web-scraper/
├── main.py              # Archivo principal
├── requirements.txt     # Dependencias
├── README.md           # Este archivo
├── LICENSE             # Licencia MIT
├── scraper.log         # Logs (generado automáticamente)
└── datos/              # Archivos de salida (generado automáticamente)
    ├── *.csv
    ├── *.json
    └── *.txt
```

## 🔍 Ejemplos de Uso

### Scraping de productos
```bash
# Ejecutar scraper
python main.py

# Configuración:
# - Proxies: No (para pruebas)
# - Delay: 1.5 segundos
# - Opción: 1 (Una URL)
# - URL: https://tienda.com/producto
# - Selectores:
#   * nombre: h1.product-name
#   * precio: .price-current
#   * stock: .stock-status
```

### Crawling de blog
```bash
# Configuración:
# - Proxies: Sí (para sitios grandes)
# - Delay: 2.0 segundos
# - Opción: 2 (Crawling)
# - URL: https://blog.ejemplo.com
# - Páginas: 100
# - Profundidad: 2
# - Selectores:
#   * titulo: h1.entry-title
#   * fecha: .entry-date
#   * contenido: .entry-content
```

## 🐛 Solución de Problemas

### Error de dependencias
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Sitio bloquea requests
- Activar proxies en configuración
- Aumentar delay entre requests
- Verificar que el sitio permita scraping

### Selectores no funcionan
- Inspeccionar HTML con herramientas de desarrollo
- Usar selectores más específicos
- Verificar que el contenido no se carga dinámicamente

### Problemas de encoding
- El scraper usa UTF-8 por defecto
- Verificar configuración regional del sistema

## 📝 Logs

Los logs se guardan automáticamente en `scraper.log`:
- Timestamp de cada operación
- URLs visitadas
- Errores encontrados
- Estadísticas de rendimiento

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## ⭐ Créditos

- Desarrollado con ❤️ para la comunidad hispana
- Inspirado en herramientas como Scrapy y BeautifulSoup
- Contribuciones bienvenidas

## 📞 Soporte

Si encuentras bugs o tienes sugerencias:
1. Revisa los logs en `scraper.log`
2. Abre un issue en GitHub
3. Incluye información detallada del error

---

**¡Dale una ⭐ si este proyecto te fue útil!**</content>
<parameter name="filePath">/Users/omanzo/VISUALSTUDIOCODE/IDK/README.md
