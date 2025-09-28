from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from datetime import datetime
import eventlet
import socket
eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_123'

# Настройки для мобильных устройств
socketio = SocketIO(
    app, 
    cors_allowed_origins="*",
    async_mode='eventlet',
    logger=True,
    engineio_logger=False
)

# Хранилище данных
messages = []
users = {}
user_count = 0

def get_local_ip():
    """Получаем локальный IP адрес"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mobile')
def mobile_version():
    """Специальный маршрут для мобильных"""
    return render_template('index.html')

@app.route('/test')
def test_connection():
    """Страница для тестирования подключения"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Тест подключения</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <h1>Тест подключения чата</h1>
        <div id="status">Проверка...</div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('connect', () => {
                document.getElementById('status').innerHTML = 
                    '<span class="success">✓ WebSocket подключен! Чат работает.</span>';
            });
            socket.on('disconnect', () => {
                document.getElementById('status').innerHTML = 
                    '<span class="error">✗ WebSocket отключен</span>';
            });
            setTimeout(() => {
                if (!socket.connected) {
                    document.getElementById('status').innerHTML = 
                        '<span class="error">✗ Не удалось подключиться к WebSocket</span>';
                }
            }, 3000);
        </script>
    </body>
    </html>
    """

@socketio.on('connect')
def handle_connect():
    global user_count
    user_count += 1
    user_agent = request.headers.get('User-Agent', 'Unknown')
    print(f'📱 Новое подключение (всего: {user_count})')
    print(f'📋 User-Agent: {user_agent}')
    
    # Отправляем историю сообщений новому клиенту
    for msg in messages:
        emit('message', msg, room=request.sid)

@socketio.on('disconnect')
def handle_disconnect():
    global user_count
    user_count -= 1
    
    # Удаляем пользователя из списка
    username = None
    for user, sid in list(users.items()):
        if sid == request.sid:
            username = user
            break
    
    if username:
        del users[username]
        emit('user_left', {
            'username': username, 
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'user_count': user_count
        }, broadcast=True)
        emit('users_update', {
            'users': list(users.keys()),
            'user_count': user_count
        }, broadcast=True)
        print(f'👋 Пользователь {username} вышел из чата')
    
    print(f'🔌 Отключение (осталось: {user_count})')

@socketio.on('join')
def handle_join(data):
    username = data['username']
    
    # Проверяем, не занято ли имя
    if username in users:
        emit('username_taken', {'message': 'Это имя уже занято'})
        return
    
    users[username] = request.sid
    
    emit('join_success', {
        'username': username,
        'user_count': user_count
    }, room=request.sid)
    
    emit('user_joined', {
        'username': username, 
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'user_count': user_count
    }, broadcast=True)
    
    emit('users_update', {
        'users': list(users.keys()),
        'user_count': user_count
    }, broadcast=True)
    
    print(f'🎉 Пользователь {username} присоединился к чату')

@socketio.on('message')
def handle_message(data):
    message_text = data['message'].strip()
    username = data['username']
    
    if not message_text:
        return
    
    message = {
        'username': username,
        'message': message_text,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'id': len(messages) + 1
    }
    
    messages.append(message)
    
    # Ограничиваем историю сообщений
    if len(messages) > 100:
        messages.pop(0)
    
    emit('message', message, broadcast=True)
    
    print(f'💬 {username}: {message_text}')

@socketio.on('typing')
def handle_typing(data):
    """Обработка индикатора набора текста"""
    emit('user_typing', {
        'username': data['username'],
        'is_typing': data['is_typing']
    }, broadcast=True, include_self=False)

if __name__ == '__main__':
    local_ip = get_local_ip()
    
    print("=" * 60)
    print("🚀 Сервер чата запущен!")
    print("=" * 60)
    print(f"📍 Локальный доступ: http://localhost:5000")
    print(f"📱 Для мобильных в Wi-Fi: http://{local_ip}:5000")
    print(f"🧪 Тест подключения: http://{local_ip}:5000/test")
    print("=" * 60)
    print("⚠️  Убедитесь, что:")
    print("   • Телефон и компьютер в одной Wi-Fi сети")
    print("   • Брандмауэр разрешает подключения на порт 5000")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    @app.route('/qr')
def qr_code():
    return render_template('qr.html')