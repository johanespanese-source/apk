// Fungsi untuk logging
function logToConsole(level, message, data = null) {
    const timestamp = new Date().toISOString();
    const logMessage = `[${timestamp}] [${level.toUpperCase()}] ${message}`;
    
    switch(level.toLowerCase()) {
        case 'error':
            console.error(logMessage);
            break;
        case 'warn':
            console.warn(logMessage);
            break;
        case 'info':
            console.info(logMessage);
            break;
        default:
            console.log(logMessage);
    }
    
    if (data) {
        console.debug('Additional data:', data);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page initialized');
    
    const loginForm = document.getElementById('loginForm');
    const registerLink = document.getElementById('registerLink');

    if (!loginForm) {
        console.error('Login form not found in DOM');
        return;
    }

    // Fungsi untuk menampilkan notifikasi
    function showNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // Event listener untuk login
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value.trim();

        // Validasi input
        if (!username || !password) {
            showNotification('Username dan password harus diisi!', 'error');
            return;
        }

        // Get CSRF token
        const csrfToken = document.querySelector('input[name="csrf_token"]').value;

        // Submit form menggunakan fetch API
        fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}&csrf_token=${encodeURIComponent(csrfToken)}`
        })
        .then(response => {
            if (response.redirected) {
                window.location.href = response.url;
                return null;
            }
            return response.json();
        })
        .then(data => {
            if (!data) return; // Skip if redirected

            if (data.success) {
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            } else {
                showNotification('Username atau password salah!', 'error');
            }
        })
        .catch(error => {
            console.error('Login error:', error);
            showNotification('Terjadi kesalahan pada server!', 'error');
        });
    });

    // Event listener untuk link register
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showNotification('Fitur pendaftaran belum tersedia. Gunakan akun demo: admin/admin123 atau user/user123', 'info');
        });
    }
});
