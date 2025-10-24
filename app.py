from flask import Flask, jsonify, request, redirect
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Función para formatear el texto de la semana
def formatear_semana(texto):
    num_semana = re.search(r'(\d+)', texto)
    anio = re.search(r'(20\d{2})', texto)
    if num_semana and anio:
        return f"{num_semana.group(1)}ª semana de {anio.group(1)}"
    return None

# Función para limpiar y convertir precios
def formatear_precio(texto):
    try:
        texto_limpio = texto.replace('€', '').replace(',', '.').strip()
        precio = float(texto_limpio)
        return round(precio, 2)
    except:
        return None

# Web scraping para obtener los precios agrícolas
def obtener_datos_agricolas():
    url_base = "https://observatorioprecios.es/mercados-alimentos-hortalizas/"
    response = requests.get(url_base)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')

    seleccion = [
        "patata", "acelga", "calabacin", "cebolla", "judia-verde-plana", "lechuga-romana",
        "pimiento-verde", "tomate-redondo-liso", "zanahoria", "limon", "manzana-golden",
        "clementina", "naranja-tipo-navel", "pera-de-agua-o-blanquilla", "platano"
    ]

    productos_encontrados = []
    mapa_agricola = {}

    for p in soup.find_all("p"):
        try:
            href = p.find("a")["href"]
            producto = href.split("/")[2]
            if producto in seleccion and producto not in productos_encontrados:
                productos_encontrados.append(producto)
        except:
            continue

    for producto in productos_encontrados:
        semanas = []
        precios = []

        try:
            url_producto = f"{url_base}/{producto}"
            response_prod = requests.get(url_producto)
            response_prod.raise_for_status()
            soup_prod = BeautifulSoup(response_prod.text, 'html.parser')
            tablas = soup_prod.find_all("table")

            if tablas:
                tabla = tablas[0]
                columnas = tabla.find_all("th")

                celdas = tabla.find_all("td")
                datos_limpios = [celda.get_text(strip=True) for celda in celdas if celda.get_text(strip=True)]

                if len(columnas) == 3:
                    for i in range(0, len(datos_limpios) - 2, 3):
                        v1, v2, v3 = datos_limpios[i:i+3]
                        if "semana" in v1.lower():
                            semana = formatear_semana(v1)
                            precio = formatear_precio(v2)
                            precio_m = formatear_precio(v3)
                        else:
                            semana = formatear_semana(v2)
                            precio = formatear_precio(v1)
                            precio_m = formatear_precio(v3)

                        if semana:
                            semanas.append(semana)
                        precios.append(precio or 0.0)
                        precios.append(precio_m or 0.0)
                else:
                    for i in range(0, len(datos_limpios) - 1, 2):
                        semana = formatear_semana(datos_limpios[i])
                        precio = formatear_precio(datos_limpios[i + 1])
                        if semana:
                            semanas.append(semana)
                        precios.append(precio or 0.0)

            mapa_agricola[producto] = {
                "Producto": producto,
                "Semanas": semanas,
                "Precios": precios
            }
        except:
            mapa_agricola[producto] = {
                "Producto": producto,
                "Semanas": [],
                "Precios": []
            }

    return list(mapa_agricola.values())

# Ruta raíz redirige automáticamente a la API JSON
@app.route('/')
def index():
    return redirect('/api/precios')

# Ruta para comprobación de Render
@app.route('/health')
def health():
    return "OK", 200

# Ruta JSON principal de precios
@app.route('/api/precios')
def api_precios_agricolas():
    producto_buscar = request.args.get('producto', '').lower()
    datos = obtener_datos_agricolas()

    if producto_buscar:
        productos_filtrados = [p for p in datos if producto_buscar in p['Producto'].lower()]
    else:
        productos_filtrados = datos

    return jsonify(productos_filtrados)

# Ejecutar en desarrollo
if __name__ == '__main__':
    app.run(debug=True)
