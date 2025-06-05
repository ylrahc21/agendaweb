from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

client = MongoClient(MONGO_URI)
db = client.agenda_app

# Estado de la app (colección: estado)
def esta_apagada():
    estado = db.estado.find_one({"nombre": "apagado"})
    return estado and estado["valor"]

@app.route('/')
def home():
    if esta_apagada():
        return render_template('apagada.html')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if esta_apagada():
        return render_template('apagada.html')
    if request.method == 'POST':
        usuario = request.form['usuario']
        contra = request.form['contra']
        user = db.usuarios.find_one({"usuario": usuario, "contra": contra})
        if user:
            session['usuario'] = usuario
            session['rol'] = user['rol']
            return redirect(url_for('dashboard'))
        return "Usuario o contraseña incorrectos"
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    citas = db.citas.find()
    return render_template('dashboard.html', citas=citas, rol=session['rol'])

@app.route('/crear_cita', methods=['POST'])
def crear_cita():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['rol'] in ['superusuario', 'admin']:
        data = {
            'nombre': request.form['nombre'],
            'telefono': request.form['telefono'],
            'fecha': request.form['fecha'],
            'hora': request.form['hora'],
            'notas': request.form.get('notas', '')
        }
        db.citas.insert_one(data)
    return redirect(url_for('dashboard'))

@app.route('/cancelar_cita/<id>')
def cancelar_cita(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
    if session['rol'] in ['superusuario', 'admin']:
        db.citas.delete_one({'_id': ObjectId(id)})
    return redirect(url_for('dashboard'))

@app.route('/apagar_app', methods=['POST'])
def apagar_app():
    if 'usuario' not in session or session['rol'] != 'superusuario':
        return redirect(url_for('login'))
    valor = request.form.get('estado') == 'apagado'
    db.estado.update_one({"nombre": "apagado"}, {"$set": {"valor": valor}}, upsert=True)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))