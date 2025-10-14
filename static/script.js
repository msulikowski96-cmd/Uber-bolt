// Funkcje mobilnego menu
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    sidebar.classList.toggle('active');
    overlay.classList.toggle('active');
}

function closeSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    sidebar.classList.remove('active');
    overlay.classList.remove('active');
}

// Zamknij sidebar po kliknięciu w link (tylko na mobile)
document.addEventListener('DOMContentLoaded', function() {
    if (window.innerWidth <= 768) {
        const sidebarLinks = document.querySelectorAll('.sidebar a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', closeSidebar);
        });
    }
});

// Funkcje obsługi celów
async function wczytajCele() {
    try {
        const response = await fetch('/cele');
        const dane = await response.json();
        
        if (dane.cele) {
            document.getElementById('input-cel-dzienny').value = dane.cele.cel_dzienny;
            document.getElementById('input-min-stawka').value = dane.cele.min_stawka;
        }
        
        if (dane.postep) {
            aktualizujPostep(dane.postep);
        }
    } catch (error) {
        console.error('Błąd wczytywania celów:', error);
    }
}

function aktualizujPostep(postep) {
    document.getElementById('cel-dzienny').textContent = postep.cel.toFixed(2) + ' zł';
    document.getElementById('postep-kwota').textContent = postep.postep.toFixed(2) + ' zł';
    document.getElementById('cel-kwota').textContent = postep.cel.toFixed(2) + ' zł';
    document.getElementById('pozostalo-kwota').textContent = postep.pozostalo.toFixed(2) + ' zł';
    document.getElementById('progress-bar').style.width = postep.procent.toFixed(1) + '%';
    
    // Zmiana koloru paska postępu
    const progressBar = document.getElementById('progress-bar');
    if (postep.procent >= 100) {
        progressBar.style.background = 'linear-gradient(90deg, #10b981, #059669)';
    } else if (postep.procent >= 75) {
        progressBar.style.background = 'linear-gradient(90deg, var(--taxi-yellow), #f59e0b)';
    } else {
        progressBar.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
    }
}

function pokazUstawieniaCelow() {
    const modal = new bootstrap.Modal(document.getElementById('modalCelow'));
    modal.show();
}

async function zapiszCele() {
    const cele = {
        cel_dzienny: document.getElementById('input-cel-dzienny').value,
        min_stawka: document.getElementById('input-min-stawka').value
    };
    
    try {
        await fetch('/cele', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(cele)
        });
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('modalCelow'));
        modal.hide();
        
        await wczytajCele();
        
        alert('✅ Cele zostały zapisane!');
    } catch (error) {
        console.error('Błąd zapisywania celów:', error);
        alert('Wystąpił błąd podczas zapisywania celów!');
    }
}

function pokazPowiadomienia(powiadomienia) {
    const container = document.getElementById('powiadomienia-container');
    container.innerHTML = '';
    
    powiadomienia.forEach(powiadomienie => {
        const div = document.createElement('div');
        div.className = `alert alert-${powiadomienie.typ} mt-3`;
        
        const strong = document.createElement('strong');
        strong.textContent = powiadomienie.tekst;
        div.appendChild(strong);
        
        container.appendChild(div);
    });
}

document.getElementById('kalkulator-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        const response = await fetch('/oblicz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const wynik = await response.json();
        
        // Aktualizacja wyników
        document.getElementById('dystans_calkowity').textContent = wynik.dystans_calkowity + ' km';
        document.getElementById('czas_calkowity_h').textContent = wynik.czas_calkowity_h + ' h';
        document.getElementById('koszt_paliwa').textContent = wynik.koszt_paliwa + ' zł';
        document.getElementById('zarobek_dla_kierowcy').textContent = wynik.zarobek_dla_kierowcy + ' zł';
        document.getElementById('zysk_netto').textContent = wynik.zysk_netto + ' zł';
        document.getElementById('stawka_godzinowa').textContent = wynik.stawka_godzinowa + ' zł/h';
        document.getElementById('ocena-text').textContent = wynik.ocena;
        
        // Aktualizacja średniej dnia
        document.getElementById('srednia-dnia').textContent = wynik.srednia_dnia + ' zł/h';
        
        // Aktualizacja postępu do celu
        if (wynik.postep) {
            aktualizujPostep(wynik.postep);
        }
        
        // Pokazanie powiadomień
        if (wynik.powiadomienia && wynik.powiadomienia.length > 0) {
            pokazPowiadomienia(wynik.powiadomienia);
        }
        
        // Zmiana koloru alertu
        const alertDiv = document.getElementById('ocena-alert');
        alertDiv.className = 'alert alert-' + wynik.ocena_klasa;
        
        // Pokazanie wyników z animacją
        const wynikiDiv = document.getElementById('wyniki');
        wynikiDiv.style.display = 'block';
        wynikiDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        
    } catch (error) {
        console.error('Błąd:', error);
        alert('Wystąpił błąd podczas obliczania!');
    }
});

// PWA Installation
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    
    // Pokaż banner instalacji jeśli użytkownik nie odrzucił go wcześniej
    if (!localStorage.getItem('pwa-banner-dismissed')) {
        document.getElementById('install-banner').style.display = 'block';
    }
});

function zainstalujPWA() {
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('Użytkownik zainstalował PWA');
            }
            deferredPrompt = null;
            document.getElementById('install-banner').style.display = 'none';
        });
    }
}

function zamknijBanner() {
    document.getElementById('install-banner').style.display = 'none';
    localStorage.setItem('pwa-banner-dismissed', 'true');
}

// Tryb ciemny
function przełączTryb() {
    const body = document.body;
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    
    body.classList.toggle('dark-mode');
    
    if (body.classList.contains('dark-mode')) {
        icon.className = 'bi bi-sun';
        text.textContent = 'Tryb jasny';
        localStorage.setItem('theme', 'dark');
    } else {
        icon.className = 'bi bi-moon-stars';
        text.textContent = 'Tryb ciemny';
        localStorage.setItem('theme', 'light');
    }
}

// Wczytanie preferencji motywu
function wczytajMotyw() {
    const savedTheme = localStorage.getItem('theme');
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        if (icon) icon.className = 'bi bi-sun';
        if (text) text.textContent = 'Tryb jasny';
    }
}

// Sprawdzanie statusu połączenia z Uber
let uberConnected = false;

async function checkUberStatus() {
    try {
        const response = await fetch('/uber/status');
        const data = await response.json();
        uberConnected = data.connected;
        
        const btn = document.getElementById('uber-btn');
        const btnText = document.getElementById('uber-btn-text');
        
        if (uberConnected) {
            btnText.textContent = 'Synchronizuj Uber';
            btn.className = 'btn btn-outline-success w-100 mb-2';
        } else {
            btnText.textContent = 'Połącz z Uber';
            btn.className = 'btn btn-outline-warning w-100 mb-2';
        }
    } catch (error) {
        console.error('Błąd sprawdzania statusu Uber:', error);
    }
}

// Obsługa kliknięcia przycisku Uber
function handleUberClick() {
    if (uberConnected) {
        syncUber();
    } else {
        window.location.href = '/uber/authorize';
    }
}

// Synchronizacja z Uber API
async function syncUber() {
    const days = prompt('Ile dni wstecz chcesz zaimportować kursy? (domyślnie 30)', '30');
    
    if (!days) return;
    
    const loadingAlert = document.createElement('div');
    loadingAlert.className = 'alert alert-info mt-3';
    loadingAlert.innerHTML = '<strong><i class="bi bi-cloud-download"></i> Synchronizacja w toku...</strong> Pobieranie kursów z Uber API...';
    document.querySelector('.main-content').prepend(loadingAlert);
    
    try {
        const response = await fetch('/uber/sync', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ days: parseInt(days) })
        });
        
        const result = await response.json();
        loadingAlert.remove();
        
        if (result.success) {
            const successAlert = document.createElement('div');
            successAlert.className = 'alert alert-success mt-3';
            successAlert.innerHTML = `<strong><i class="bi bi-check-circle"></i> Sukces!</strong> ${result.message}`;
            document.querySelector('.main-content').prepend(successAlert);
            
            setTimeout(() => successAlert.remove(), 5000);
            
            await wczytajCele();
        } else {
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger mt-3';
            errorAlert.innerHTML = `<strong><i class="bi bi-x-circle"></i> Błąd!</strong> ${result.message}`;
            document.querySelector('.main-content').prepend(errorAlert);
            
            setTimeout(() => errorAlert.remove(), 5000);
        }
    } catch (error) {
        loadingAlert.remove();
        alert('Wystąpił błąd podczas synchronizacji: ' + error.message);
    }
}

// Rejestracja Service Workera
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/static/service-worker.js')
        .then(registration => {
            console.log('Service Worker zarejestrowany:', registration);
        })
        .catch(error => {
            console.log('Błąd rejestracji Service Workera:', error);
        });
}

// Wczytanie danych przy starcie
window.addEventListener('load', async function() {
    // Wczytaj motyw
    wczytajMotyw();
    
    // Sprawdź status połączenia z Uber
    await checkUberStatus();
    
    // Wczytaj cele
    await wczytajCele();
    
    // Wczytaj średnią dnia
    try {
        const response = await fetch('/srednia_dnia');
        const dane = await response.json();
        if (dane.srednia_dnia !== 'Brak danych') {
            document.getElementById('srednia-dnia').textContent = dane.srednia_dnia + ' zł/h';
        }
    } catch (error) {
        console.log('Nie udało się wczytać średniej dnia');
    }
});
