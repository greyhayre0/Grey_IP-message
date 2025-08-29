import os
import socket
import random
from flask import render_template, request, jsonify, send_from_directory, current_app

messages = []
ip_names = {}

def generate_name():
    adjectives = ['Смелый', 'Изобретательный', 'Мелкий', 'Бесподобный', 'Гениальный', 'Загадочный', 'Бородатый', 'Грязный']
    nouns = ['Засранец', 'Касипор', 'Алкаш', 'Вандал', 'Задрот', 'Тормоз', 'Очконавт', 'Бездарь']
    return f"{random.choice(adjectives)} {random.choice(nouns)}"

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

def init_routes(app):
    @app.route('/')
    def index():
        ip = get_ip()
        return render_template('index.html', ip=ip)

    @app.route('/get_messages')
    def get_messages():
        return jsonify({'messages': messages})

    @app.route('/send_message', methods=['POST'])
    def send_message():
        data = request.get_json()
        text = data.get('text', '')
        ip = request.remote_addr
        if ip not in ip_names:
            ip_names[ip] = generate_name()
        sender_name = ip_names[ip]
        messages.append({'sender': sender_name, 'text': text})
        return jsonify({'status': 'ok'})

    @app.route('/upload', methods=['POST'])
    def upload():
        if 'file' not in request.files:
            return jsonify({'message': 'Нет файла'}), 400
        file = request.files['file']
        filename = file.filename
        name_part, ext = os.path.splitext(filename)
        if len(name_part) > 10:
            name_part = name_part[:10]
        filename = name_part + ext
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return jsonify({'message': 'Файл загружен'})

    @app.route('/list_files')
    def list_files():
        try:
            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 20))
            if page < 1:
                page = 1
        except:
            page = 1
            per_page = 20

        all_items = []
        upload_folder = current_app.config['UPLOAD_FOLDER']
        for name in os.listdir(upload_folder):
            path = os.path.join(upload_folder, name)
            if os.path.isdir(path):
                total_size = 0
                for root, dirs, files in os.walk(path):
                    for f in files:
                        fp = os.path.join(root, f)
                        if os.path.isfile(fp):
                            total_size += os.path.getsize(fp)
                if total_size < 1024:
                    size_str = f"{total_size} байт"
                elif total_size < 1024*1024:
                    size_str = f"{total_size/1024:.2f} Кб"
                else:
                    size_str = f"{total_size/(1024*1024):.2f} Мб"
                all_items.append({'name': name + '/', 'size': size_str, 'is_dir': True})
            else:
                size = os.path.getsize(path)
                if size < 1024:
                    size_str = f"{size} байт"
                elif size < 1024*1024:
                    size_str = f"{size/1024:.2f} Кб"
                else:
                    size_str = f"{size/(1024*1024):.2f} Мб"
                all_items.append({'name': name, 'size': size_str, 'is_dir': False})

        total_pages = (len(all_items) + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        page_items = all_items[start:end]

        return jsonify({'items': page_items, 'total_pages': total_pages})

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)