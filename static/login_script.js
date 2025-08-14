document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerLink = document.getElementById('registerLink');

    // Data akun demo (hanya untuk simulasi)
    const demoUsers = [
        { id: 1, username: "admin", password: "admin123", role: "admin" },
        { id: 2, username: "user", password: "user123", role: "user" }
    ];

    // Fungsi untuk menampilkan notifikasi
    function showNotification(message, type = 'info') {
        // Hapus notifikasi lama
        document.querySelectorAll('.notification').forEach(n => n.remove());

        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('hide');
            notification.addEventListener('transitionend', () => notification.remove(), { once: true });
        }, 3000);
    }

    // Event listener untuk login
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();

            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();

            const user = demoUsers.find(u => u.username === username && u.password === password);
console.log(user)
           if (user) {
    localStorage.setItem('currentUser', JSON.stringify(user));
    showNotification('Login berhasil! Mengarahkan ke halaman utama...', 'success');

    setTimeout(() => {
        window.location.href = 'index.html';
    }, 2000);

            } else {
                showNotification('Username atau password salah!', 'error');
            }
        });
    }

    // Event listener untuk link register
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showNotification('Fitur pendaftaran belum tersedia. Gunakan akun demo: admin/admin123 atau user/user123', 'info');
        });
    }
});
