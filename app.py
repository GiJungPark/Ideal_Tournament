from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit
import os
from werkzeug.utils import secure_filename
import random
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ideal_types = []
chosen_ideals = []

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_matches():
    # Filter out already chosen and remaining images
    remaining_images = [ideal for ideal in ideal_types if ideal['name'] not in chosen_ideals]
    return random.sample(remaining_images, 2)

def save_uploaded_file(file, name):
    # Remove special characters and spaces from Korean name
    cleaned_name = re.sub(r'[^\w\s]', '', name)
    filename = f"{cleaned_name}.{file.filename.rsplit('.', 1)[1].lower()}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    return filename

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        ideal_name = request.form['name']
        filename = save_uploaded_file(file, ideal_name)
        ideal_types.append({'name': ideal_name, 'image': filename})
        socketio.emit('update_images', {'images': [i['name'] for i in ideal_types]})
        if len(ideal_types) >= 8:
            return redirect(url_for('game'))
    return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    emit('update_images', {'images': [i['name'] for i in ideal_types]})


@app.route('/game', methods=['GET', 'POST'])
def game():
    if request.method == 'GET':
        session.clear()

    if 'matches' not in session:
        session['matches'] = generate_matches()
        chosen_ideals.clear()

    matches = session['matches']

    if request.method == 'POST':
        chosen_ideal = request.form['chosen_ideal']
        chosen_ideals.append(chosen_ideal)

        if len(chosen_ideals) < min(len(ideal_types), 8) - 1:
            session['matches'] = generate_matches()
        else:
             return render_template('game.html', matches=[], chosen_ideals=chosen_ideals)

    return render_template('game.html', matches=matches)

@app.route('/result')
def result():
    return render_template('result.html', chosen_ideals=chosen_ideals)


if __name__ == '__main__':
    app.run(debug=True)