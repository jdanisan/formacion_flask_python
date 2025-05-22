from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

# Modelo de la base de datos
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Integer, default=0)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id

# Ruta principal
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

# Función de scraping estructurado
def obtener_datos_agricolas():
    url_base = "https://observatorioprecios.es/alimentos-frescos"
    seleccion = [
        "patata", "acelga", "calabacin", "cebolla", "judia-verde-plana", "lechuga-romana",
        "pimiento-verde", "tomate-redondo-liso", "zanahoria", "limon", "manzana-golden",
        "clementina", "naranja-tipo-navel", "pera-de-agua-o-blanquilla", "platano"
    ]

    response = requests.get(url_base)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
    productos_scrapeados = {}
    enlaces_productos = []

    # Buscar enlaces a productos seleccionados
    for p in soup.find_all("p"):
        try:
            href = p.find_all("a")[0]["href"]
            nombre_producto = href.split("/")[2]
            if nombre_producto in seleccion:
                enlaces_productos.append(nombre_producto)
        except:
            continue

    # Scraping de cada producto
    for producto in enlaces_productos:
        url_producto = f"{url_base}/{producto}"
        html_producto = requests.get(url_producto).text
        soup_producto = BeautifulSoup(html_producto, 'html.parser')
        tabla = soup_producto.find("table")
        if not tabla:
            continue

        productos_scrapeados[producto] = {}

        for fila in tabla.find_all("tr")[1:]:
            celdas = fila.find_all("td")
            if len(celdas) >= 2:
                semana = celdas[0].text.strip()
                precio = celdas[1].text.strip().replace(",", ".")
                try:
                    productos_scrapeados[producto][semana] = float(precio)
                except:
                    productos_scrapeados[producto][semana] = None

    return productos_scrapeados

# Ruta para mostrar precios agrícolas
@app.route('/precios', methods=['GET'])
def precios_agricolas():
    producto_buscar = request.args.get('producto', '').lower()
    datos = obtener_datos_agricolas()

    if producto_buscar:
        datos_filtrados = {k: v for k, v in datos.items() if producto_buscar in k.lower()}
    else:
        datos_filtrados = datos

    if not datos_filtrados:
        return render_template('precios.html', productos={}, mensaje="No se encontraron productos que coincidan con la búsqueda.")

    return render_template('precios.html', productos=datos_filtrados)

# Crear la base de datos
with app.app_context():
    db.create_all()

# Ejecutar la app
if __name__ == "__main__":
    app.run(debug=True)
