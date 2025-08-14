from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, url_for, flash, session
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf.csrf import CSRFProtect
import pymysql
import pymysql.cursors
import os
import logging
from logging.handlers import RotatingFileHandler

# Konfigurasi logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] - %(message)s'
))
logger.addHandler(handler)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key_here'  # Ganti dengan kunci rahasia yang kuat

# Konfigurasi CSRF
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_SECRET_KEY'] = 'csrf_secret_key_here'  # Ganti dengan kunci rahasia yang berbeda
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # Token berlaku selama 1 jam
csrf = CSRFProtect()
csrf.init_app(app)

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

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.name = user_data['name']

@login_manager.user_loader
def load_user(user_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            user_data = cursor.fetchone()
        if user_data:
            return User(user_data)
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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        # Verify CSRF token for both AJAX and regular form submissions
        token = request.form.get('csrf_token')
        if not token:
            token = request.headers.get('X-CSRFToken')
        if not token:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'CSRF token missing'}), 400
            flash('CSRF token missing', 'error')
            return render_template('login.html')
            
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if not username or not password:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': 'Username dan password harus diisi!'}), 400
            flash('Username dan password harus diisi!', 'error')
            return render_template('login.html')
        
        try:
            connection = get_db_connection()
            logger.info(f"Login attempt for username: {username}")
            logger.debug("Database connection established")
            
            with connection.cursor() as cursor:
                # Langsung periksa username dan password tanpa hashing
                query = 'SELECT * FROM users WHERE username = %s AND password = %s'
                cursor.execute(query, (username, password))
                logger.debug(f"Executing query: {query} with username={username}")
                account = cursor.fetchone()
                logger.debug(f"Query result: {account}")
                
                if account:
                    user = User(account)
                    login_user(user)
                    logger.info(f'Login successful for user: {username}')
                    
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': True,
                            'message': 'Login berhasil!',
                            'redirect': url_for('index')
                        })
                    
                    flash('Login berhasil!', 'success')
                    return redirect(url_for('index'))
                else:
                    logger.warning(f'Failed login attempt for username: {username}')
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'success': False,
                            'error': 'Username atau password salah!'
                        }), 401
                    
                    flash('Username atau password salah!', 'error')
        
        except Exception as e:
            logger.error(f'Database error during login: {str(e)}')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'error': 'Terjadi kesalahan pada server'
                }), 500
            flash('Terjadi kesalahan pada server', 'error')
            return render_template('login.html')
        
        finally:
            if 'connection' in locals():
                connection.close()
                logger.debug('Database connection closed')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('login'))

# Route untuk mengecek database
@app.route('/check_db')
def check_db():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Check if users table exists
            cursor.execute("SHOW TABLES LIKE 'users'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                # Get table structure
                cursor.execute("DESCRIBE users")
                structure = cursor.fetchall()
                
                # Get user count
                cursor.execute("SELECT COUNT(*) as count FROM users")
                count = cursor.fetchone()['count']
                
                return jsonify({
                    'success': True,
                    'table_exists': True,
                    'structure': structure,
                    'user_count': count
                })
            else:
                # Create users table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(100) NOT NULL,
                        name VARCHAR(100) NOT NULL
                    )
                """)
                
                # Insert a default admin user
                cursor.execute("""
                    INSERT INTO users (username, password, name)
                    VALUES ('admin', 'admin123', 'Administrator')
                """)
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Users table created with default admin user',
                    'credentials': {
                        'username': 'admin',
                        'password': 'admin123'
                    }
                })
    except Exception as e:
        logger.error(f"Database check error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        connection.close()

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
@csrf.exempt
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