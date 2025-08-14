from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, url_for, flash, session
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import pymysql
import pymysql.cursors
import os
import uuid

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key_here'  # Ganti dengan kunci rahasia yang kuat

# Konfigurasi MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Sesuaikan dengan password MySQL Anda
app.config['MYSQL_DB'] = 'flask_login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# Fungsi untuk mendapatkan koneksi database
def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

# Konfigurasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Dictionary untuk menyimpan session token aktif
active_sessions = {}

class User(UserMixin):
    def __init__(self, user_id, username, name):
        self.id = user_id
        self.username = username
        self.name = name

@login_manager.user_loader
def load_user(user_id):
    # Periksa apakah session token valid
    if user_id in active_sessions and session.get('session_token') == active_sessions[user_id]:
        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
                user_data = cursor.fetchone()
            if user_data:
                return User(user_data['id'], user_data['username'], user_data['name'])
        finally:
            connection.close()
    return None

# Simulasi status perangkat
device_status = {
    "presence": False,
    "light_level": 0,
    "dimmer_power": 0,
    "brightness": 10,
    "auto_control": False
}

# ================== ROUTE AUTHENTICATION ================== #
@app.route('/login', methods=['GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/verify-login', methods=['GET'])
def verify_login():
    username = request.form.get('username')
    password = request.form.get('password')

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
            account = cursor.fetchone()

        if account:
            # Verifikasi password (SHA2)
            with connection.cursor() as cursor:
                cursor.execute('SELECT SHA2(%s, 256) = %s AS password_match',
                               (password, account['password']))
                result = cursor.fetchone()
                password_match = result['password_match']

            if password_match:
                user_id = str(account['id'])

                # Logout sesi sebelumnya jika ada
                if user_id in active_sessions:
                    del active_sessions[user_id]
                    flash('Sesi sebelumnya telah diakhiri karena login dari perangkat baru.', 'info')

                # Buat session token baru
                session_token = str(uuid.uuid4())
                active_sessions[user_id] = session_token
                session['session_token'] = session_token

                user = User(account['id'], account['username'], account['name'])
                login_user(user)
                flash('Login berhasil!', 'success')
                return redirect(url_for('index'))

        flash('Username atau password salah!', 'danger')
    finally:
        connection.close()

    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    user_id = str(current_user.id)
    
    # Hapus session token
    if user_id in active_sessions:
        del active_sessions[user_id]
    
    if 'session_token' in session:
        del session['session_token']
    
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# ================== PROTECTED ROUTES ================== #
@app.route('/')
@login_required
def index():
    """Menampilkan halaman utama"""
    return render_template('index.html', username=current_user.name)

@app.route('/static/<path:path>')
def serve_static(path):
    """Menyajikan file statis (CSS, JS, dll)"""
    return send_from_directory('static', path)

# Endpoint untuk ESP32: POST sensor data
@app.route('/update_esp32_status', methods=['POST'])
def update_esp32_status():
    """Endpoint untuk menerima data sensor dari ESP32"""
    data = request.json
    
    # Update status perangkat dengan data dari ESP32
    if 'presence' in data:
        device_status['presence'] = data['presence']
    if 'light_level' in data:
        device_status['light_level'] = data['light_level']
    if 'dimmer_power' in data:
        device_status['dimmer_power'] = data['dimmer_power']
    if 'lamp_state' in data:
        pass  # Tidak disimpan secara langsung
        
    print(f"Received sensor data: Presence={data.get('presence')}, Light={data.get('light_level')} lux, Power={data.get('dimmer_power')}%")
    
    return jsonify({"status": "success", "message": "Data sensor diterima"})

# Endpoint untuk ESP32: GET control settings
@app.route('/get_desired_control', methods=['GET'])
def get_desired_control():
    """Endpoint untuk memberikan data kontrol ke ESP32"""
    return jsonify({
        "auto_control": device_status["auto_control"],
        "brightness": device_status["brightness"]
    })

# Endpoint untuk web interface: GET status
@app.route('/api/status', methods=['GET'])
@login_required
def get_status():
    """Endpoint untuk mendapatkan status sensor (untuk web)"""
    return jsonify({
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "presence": device_status['presence'],
        "light_level": device_status['light_level'],
        "dimmer_power": device_status['dimmer_power'],
        "brightness": device_status['brightness'],
        "auto_control": device_status['auto_control']
    })

# Endpoint untuk web interface: POST control
@app.route('/api/control', methods=['POST'])
@login_required
def control_device():
    """Endpoint untuk mengontrol perangkat (dari web)"""
    data = request.json
    
    if 'brightness' in data:
        device_status['brightness'] = data['brightness']
    
    if 'auto_control' in data:
        device_status['auto_control'] = data['auto_control']
    
    print(f"Control updated: Auto={data.get('auto_control')}, Brightness={data.get('brightness')}%")
    
    return jsonify({
        "status": "success",
        "message": "Perintah berhasil diproses",
        "new_state": device_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)