document.addEventListener('DOMContentLoaded', function() {
    // Referensi elemen DOM
    const updateTimeElement = document.getElementById('update-time');
    const presenceValue = document.getElementById('presence-value');
    const presenceIndicator = document.getElementById('presence-indicator');
    const lightLevel = document.getElementById('light-level');
    const luxProgress = document.getElementById('lux-progress');
    const lampStatus = document.getElementById('lamp-status');
    const lightProgress = document.getElementById('light-progress');
    const modeSwitch = document.getElementById('mode-switch');
    const manualLabel = document.getElementById('manual-label');
    const autoLabel = document.getElementById('auto-label');
    const brightnessSlider = document.getElementById('brightness-slider');
    const brightnessValue = document.getElementById('brightness-value');
    const decreaseBtn = document.getElementById('decrease-btn');
    const increaseBtn = document.getElementById('increase-btn');
    const powerBtn = document.getElementById('power-btn');
    const optimalBtn = document.getElementById('optimal-btn');
    const maxBtn = document.getElementById('max-btn');
    const lampIcon = document.getElementById('lamp-icon');
    const intensityFill = document.getElementById('intensity-fill');
    const intensityText = document.getElementById('intensity-text');

    // Variabel state
    let currentBrightness = 0;
    let isAutoMode = false;
    let isSendingCommand = false;

    // Fungsi untuk memperbarui UI
    async function updateUI() {
        try {
            const response = await fetch('/api/status');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            
            // Perbarui "Terakhir diperbarui"
            if (data.timestamp) {
                updateTimeElement.textContent = `Terakhir diperbarui: ${data.timestamp}`;
            } else {
                updateTimeElement.textContent = 'Memuat...';
            }

            // Perbarui Status Kehadiran
            presenceValue.textContent = data.presence ? "Terdeteksi" : "Tidak Ada";
            presenceIndicator.classList.toggle('active', data.presence);

            // Perbarui Intensitas Cahaya
            lightLevel.textContent = `${data.light_level} lux`;
            const luxPercentage = Math.min(100, (data.light_level / 1000) * 100);
            luxProgress.style.width = `${luxPercentage}%`;

            // Perbarui Status Lampu
            lampStatus.textContent = `${data.dimmer_power}%`;
            lightProgress.style.width = `${data.dimmer_power}%`;

            // Perbarui Visual Lampu
            const lampOn = data.dimmer_power > 0;
            lampIcon.classList.toggle('on', lampOn);
            lampIcon.classList.toggle('off', !lampOn);
            intensityFill.style.width = `${data.dimmer_power}%`;
            intensityText.textContent = `${data.dimmer_power}%`;

            // Perbarui Mode Kontrol
            isAutoMode = data.auto_control;
            modeSwitch.checked = isAutoMode;
            if (isAutoMode) {
                manualLabel.classList.remove('active');
                autoLabel.classList.add('active');
                brightnessSlider.disabled = true;
                decreaseBtn.disabled = true;
                increaseBtn.disabled = true;
                powerBtn.disabled = true;
                optimalBtn.disabled = true;
                maxBtn.disabled = true;
            } else {
                manualLabel.classList.add('active');
                autoLabel.classList.remove('active');
                brightnessSlider.disabled = false;
                decreaseBtn.disabled = false;
                increaseBtn.disabled = false;
                powerBtn.disabled = false;
                optimalBtn.disabled = false;
                maxBtn.disabled = false;
            }

            // Perbarui Slider Kecerahan
            brightnessSlider.value = data.brightness;
            brightnessValue.textContent = `${data.brightness}%`;
            currentBrightness = data.brightness;
            
        } catch (error) {
            console.error('Gagal mengambil data:', error);
            showNotification('Gagal memuat data terbaru', 'error');
        }
    }

    // Fungsi untuk mengirim perintah kontrol ke server
    async function sendControlCommand(payload) {
        if (isSendingCommand) {
            console.log('Masih mengirim perintah sebelumnya, abaikan...');
            return;
        }
        
        isSendingCommand = true;
        try {
            const response = await fetch('/api/control', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            console.log('Response dari server:', result);
            
            // Perbarui UI dengan data terbaru dari server setelah perintah berhasil
            await updateUI();
            showNotification('Perintah kontrol berhasil dikirim!');
            
        } catch (error) {
            console.error('Gagal mengirim perintah:', error);
            showNotification('Gagal mengirim perintah kontrol', 'error');
            
            // Jika gagal, kembalikan switch ke state sebelumnya
            if (payload.auto_control !== undefined) {
                modeSwitch.checked = !payload.auto_control;
            }
        } finally {
            isSendingCommand = false;
        }
    }

    // Event Listener untuk Mode Kontrol
    modeSwitch.addEventListener('change', function() {
        const newAutoMode = this.checked;
        
        // Hanya kirim jika ada perubahan
        if (newAutoMode !== isAutoMode) {
            sendControlCommand({
                auto_control: newAutoMode,
                brightness: currentBrightness // Pertahankan brightness saat ini
            });
        }
    });

    // Event Listener untuk Slider Kecerahan
    brightnessSlider.addEventListener('input', function() {
        if (!isAutoMode) {
            const newBrightness = parseInt(this.value);
            currentBrightness = newBrightness;
            brightnessValue.textContent = `${newBrightness}%`;
            intensityFill.style.width = `${newBrightness}%`;
            intensityText.textContent = `${newBrightness}%`;
            
            if (newBrightness > 0) {
                lampIcon.classList.add('on');
                lampIcon.classList.remove('off');
            } else {
                lampIcon.classList.remove('on');
                lampIcon.classList.add('off');
            }
        }
    });

    // Event Listener untuk saat slider dilepas
    brightnessSlider.addEventListener('change', function() {
        if (!isAutoMode) {
            sendControlCommand({
                brightness: parseInt(this.value)
            });
        }
    });

    // Kontrol Tombol
    decreaseBtn.addEventListener('click', function() {
        if (!isAutoMode && !this.disabled) {
            currentBrightness = Math.max(0, parseInt(brightnessSlider.value) - 10);
            brightnessSlider.value = currentBrightness;
            brightnessValue.textContent = `${currentBrightness}%`;
            sendControlCommand({
                brightness: currentBrightness
            });
        }
    });

    increaseBtn.addEventListener('click', function() {
        if (!isAutoMode && !this.disabled) {
            currentBrightness = Math.min(100, parseInt(brightnessSlider.value) + 10);
            brightnessSlider.value = currentBrightness;
            brightnessValue.textContent = `${currentBrightness}%`;
            sendControlCommand({
                brightness: currentBrightness
            });
        }
    });

    powerBtn.addEventListener('click', function() {
        if (!isAutoMode && !this.disabled) {
            currentBrightness = 0;
            brightnessSlider.value = 0;
            brightnessValue.textContent = '0%';
            sendControlCommand({
                brightness: 0
            });
        }
    });

    optimalBtn.addEventListener('click', function() {
        if (!isAutoMode && !this.disabled) {
            currentBrightness = 50;
            brightnessSlider.value = 50;
            brightnessValue.textContent = '50%';
            sendControlCommand({
                brightness: 50
            });
        }
    });

    maxBtn.addEventListener('click', function() {
        if (!isAutoMode && !this.disabled) {
            currentBrightness = 100;
            brightnessSlider.value = 100;
            brightnessValue.textContent = '100%';
            sendControlCommand({
                brightness: 100
            });
        }
    });

    // Toggle lampu saat diklik
    lampIcon.addEventListener('click', function() {
        if (!isAutoMode) {
            const newValue = currentBrightness > 0 ? 0 : 50;
            brightnessSlider.value = newValue;
            brightnessSlider.dispatchEvent(new Event('input'));
            sendControlCommand({
                brightness: newValue
            });
        }
    });

    // Fungsi notifikasi
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Hapus setelah 3 detik
        setTimeout(() => {
            notification.classList.add('hide');
            notification.addEventListener('transitionend', () => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, { once: true });
        }, 3000);
    }

    // Ambil status setiap 3 detik
    setInterval(updateUI, 3000);
    // Panggil pertama kali untuk inisialisasi
    updateUI();
});