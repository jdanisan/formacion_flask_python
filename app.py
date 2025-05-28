
from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# Definición de la clase Todo para la base de datos
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

# Ruta principal para manejar tareas
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == "POST":
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f'There was an issue adding your task: {e}'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        return render_template('index.html', tasks=tasks)

# Ruta para eliminar tareas
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except Exception as e:
        return f'There was a problem deleting that task: {e}'

# Ruta para actualizar tareas
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task.content = request.form['content']

        try:
            db.session.commit()
            return redirect('/')
        except Exception as e:
            return f'There was a problem with the update of the task: {e}'
    else:
        return render_template('update.html', task=task)

# Función que hace web scraping y obtiene los datos agrícolas
#def obtener_datos_agricolas():
#    url = "https://observatorioprecios.es/alimentos-frescos/"  # URL para scraping
#
#    response = requests.get(url)
#    response.raise_for_status()     
#    soup = BeautifulSoup(response.text, 'html.parser')    
#    product_refs = soup.find_all("p")
#    products = []
#    seleccion=["patata","acelga","calabacin","cebolla","judia-verde-plana","lechuga-romana","pimiento-verde",
#               "tomate-redondo-liso","zanahoria","limon","manzana-golden","clementina",
#               "naranja-tipo-navel","pera-de-agua-o-blanquilla","platano"]
#    
#    for p in product_refs:
#        try:
#            t = p.find_all("a")[0]["href"].split("/")[2]
#            for i in range(len(seleccion)):
#                if seleccion[i]==t: 
#                    products.append(t)
#        except:
#            pass
#    #products.pop(-1)
#    
#    #precios_agro=[]
#    #semanas=[]
#    #columns=[]
#    #n=0
#    #for i in range(len(products)):
#    #    product_url=f"{url}/{products[i]}"
#    #    table = BeautifulSoup(requests.get(product_url).text, 'html.parser').find_all("table")
#    #    columns=table[0].find_all("th")
#    #    if len(columns)>2:
#    #        for n in range(len(seleccion)):
#    #            #print(seleccion[n])
#    #            for t in table[0]:
#    #                try:
#    #                    for i in range(1,len(t),3):
#    #                        t2 = t.find_all("td")[i]
#    #                        precios_agro.append(t2.contents)
##
#    #                    for i2 in range(0,len(t),3):
#    #                        t3= t.find_all("td")[i2]
#    #                        semanas.append(t3.contents)    
#    #                except:
#    #                    
#    
#    precios_agro=[]
#    semanas=[]
#    columns=[]
#    n=0
#    for i in range(len(products)):
#        product_url=f"{url}/{products[i]}"
#        table = BeautifulSoup(requests.get(product_url).text, 'html.parser').find_all("table")
#        columns=table[0].find_all("th")
#        if len(columns)>2:
#            for n in range(len(seleccion)):
#                print(seleccion[n])
#                for t in table[0]:
#                    try:
#                        for i in range(1,len(t),3):
#                            t2 = t.find_all("td")[i]
#                            precios_agro.append(t2.contents)
#
#                        for i2 in range(0,len(t),3):
#                            t3= t.find_all("td")[i2]
#                            semanas.append(t3.contents)    
#                    except:
#                        pass
import re
def formatear_semana(texto):
    num_semana = re.search(r'(\d+)', texto)
    anio = re.search(r'(20\d{2})', texto)

    if num_semana and anio:
        return f"{num_semana.group(1)}ª semana de {anio.group(1)}"
    else:
        return None  # Indicar que no es válido      

def formatear_precio(texto):
    """
    Limpia y convierte un texto de precio a un formato estándar.
    Devuelve None si el contenido no es válido.
    """
    try:
        # Eliminar símbolos como € y convertir comas a puntos para decimales
        texto_limpio = texto.replace('€', '').replace(',', '.').strip()

        # Convertir a float para asegurar que es un número válido
        precio = float(texto_limpio)
        return round(precio, 2)  # Redondea a dos decimales
    except:
        return None  # Precio no válido

                    
def obtener_datos_agricolas():
    url_base = "https://observatorioprecios.es/alimentos-frescos"
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
    contador = 0

    # Buscar enlaces válidos
    for p in soup.find_all("p"):
        try:
            href = p.find("a")["href"]
            producto = href.split("/")[2]
            if producto in seleccion and producto not in productos_encontrados:
                productos_encontrados.append(producto)
        except Exception:
            continue

    # Recorrer productos encontrados
    for producto in productos_encontrados:
        if contador >= 15:
            break

        semanas = []
        precios = []
        #print(f"Procesando producto: {producto}")

        try:
            url_producto = f"{url_base}/{producto}"
            response_prod = requests.get(url_producto)
            response_prod.raise_for_status()
            soup_prod = BeautifulSoup(response_prod.text, 'html.parser')
            tablas = soup_prod.find_all("table")

            if tablas:
                tabla = tablas[0]
                columnas = tabla.find_all("th")
                #print("hola2")

                # Si hay más de 2 columnas usamos el método extendido
                if len(columnas) ==3:
                    
                     # Modo alternativo (cuando las celdas <td> están sin <tr>)
                    celdas = tabla.find_all("td")
                    datos_limpios = [celda.get_text(strip=True) for celda in celdas if celda.get_text(strip=True)]

                    for i in range(0, len(datos_limpios) - 2, 3):
                        valor1 = datos_limpios[i]
                        valor2 = datos_limpios[i +1]
                        valor3 = datos_limpios[i + 2]

                        if "semana" in valor1.lower():
                            semana = formatear_semana(valor1)
                            precio = formatear_precio(valor2)
                            precio_m= formatear_precio(valor3)
                        else:
                            semana = formatear_semana(valor2)
                            precio = formatear_precio(valor1)
                            precio_m=formatear_precio(valor3)

                        if not (semana.__eq__("None")):
                            semanas.append(semana)
                        #print (semana)
                        
                        precio = precio if precio is not None else 0.0  # o "No disponible"
                        precio_m = precio_m if precio_m is not None else 0.0
                        
                        precios.append(precio)
                        precios.append(precio_m)
                        i=i+1
                        
                        
                        
                        
                else:
                    # Modo alternativo (cuando las celdas <td> están sin <tr>)
                    celdas = tabla.find_all("td")
                    datos_limpios = [celda.get_text(strip=True) for celda in celdas if celda.get_text(strip=True)]

                    for i in range(0, len(datos_limpios) - 1, 2):
                        valor1 = datos_limpios[i]
                        valor2 = datos_limpios[i + 1]
                        

                        if "semana" in valor1.lower():
                            semana = valor1
                            precio = valor2     
                        else:
                            semana = valor2
                            precio = valor1    

                        semanas.append(semana)
                        precios.append(precio)  
            else:
                print(f"No se encontró tabla para {producto}")

            mapa_agricola[producto] = {
                "Producto": producto,
                "Semanas": semanas,
                "Precios": precios
            }
            contador += 1

        except Exception as e:
            print(f"Error con {producto}: {e}")
            mapa_agricola[producto] = {
                "Producto": producto,
                "Semanas": semanas,
                "Precios": precios
            }

            continue

    return list(mapa_agricola.values())


  
    
                


    

# Ruta para obtener los precios agrícolas
@app.route('/precios', methods=['GET'])
def precios_agricolas():
    # Obtener el parámetro 'producto' de la búsqueda (si existe)
    producto_buscar = request.args.get('producto', '').lower()

    # Obtener los datos de productos desde la función de scraping
    datos = obtener_datos_agricolas()
    print (datos)
    print('se estan escribiendo datos')

    # Verifica si no obtuviste datos
    #if "error" in datos:
    #    return jsonify(datos), 500  # Esto devolvería un mensaje de error si no se pudieron obtener los productos
#
    # Filtrar los productos si se proporcionó un término de búsqueda
    if producto_buscar:
        print('Busqueda ejecutandose')
        productos_filtrados = [producto for producto in datos if producto_buscar in producto['Producto'].lower()]
    else:
        productos_filtrados = datos

    # Si no se encuentran productos, mostrar un mensaje en la plantilla
    if not productos_filtrados:
        return render_template('precios.html', productos=[], mensaje="No se encontraron productos que coincidan con la búsqueda.")

    return render_template('precios.html', productos=productos_filtrados)

@app.route('/api/precios', methods=['GET'])
def api_precios_agricolas():
    producto_buscar = request.args.get('producto', '').lower()
    datos = obtener_datos_agricolas()

    if producto_buscar:
        productos_filtrados = [producto for producto in datos if producto_buscar in producto['Producto'].lower()]
    else:
        productos_filtrados = datos

    return jsonify(productos_filtrados)


# Crear la base de datos si no existe
with app.app_context():
    db.create_all()

# Ejecutar la aplicación Flask
if __name__ == "__main__":
    app.run(debug=True)
    

