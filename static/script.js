// Funkcje mobilnego menu - globalne, aby działały z onclick w HTML
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

// Inicjalizacja po załadowaniu DOM
document.addEventListener('DOMContentLoaded', function() {
    // Zamknij sidebar po kliknięciu w link (tylko na mobile)
    if (window.innerWidth <= 768) {
        const sidebarLinks = document.querySelectorAll('.sidebar a');
        sidebarLinks.forEach(link => {
            link.addEventListener('click', closeSidebar);
        });
    }

    // Inicjalizacja formularza kalkulatora tylko jeśli istnieje
    const kalkulatorForm = document.getElementById('kalkulator-form');
    if (kalkulatorForm) {
        kalkulatorForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const formData = new FormData(this);
            const data = {};
            formData.forEach((value, key) => {
                data[key] = value;
            });

            // Dodanie obsługi pola płatności gotówką
            data.platnosc_gotowka = document.getElementById('platnosc_gotowka').checked ? 'tak' : 'nie';


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
    }
});

// Funkcje obsługi celów
async function wczytajCele() {
    try {
        const response = await fetch('/cele');
        const dane = await response.json();

        if (dane.cele) {
            const inputCelDzienny = document.getElementById('input-cel-dzienny');
            const inputMinStawka = document.getElementById('input-min-stawka');

            if (inputCelDzienny) inputCelDzienny.value = dane.cele.cel_dzienny;
            if (inputMinStawka) inputMinStawka.value = dane.cele.min_stawka;
        }

        if (dane.postep) {
            aktualizujPostep(dane.postep);
        }
    } catch (error) {
        console.error('Błąd wczytywania celów:', error);
    }
}

function aktualizujPostep(postep) {
    const celDzienny = document.getElementById('cel-dzienny');
    const postepKwota = document.getElementById('postep-kwota');
    const celKwota = document.getElementById('cel-kwota');
    const pozostaloKwota = document.getElementById('pozostalo-kwota');
    const progressBar = document.getElementById('progress-bar');

    if (celDzienny) celDzienny.textContent = postep.cel.toFixed(2) + ' zł';
    if (postepKwota) postepKwota.textContent = postep.postep.toFixed(2) + ' zł';
    if (celKwota) celKwota.textContent = postep.cel.toFixed(2) + ' zł';
    if (pozostaloKwota) pozostaloKwota.textContent = postep.pozostalo.toFixed(2) + ' zł';
    if (progressBar) {
        progressBar.style.width = postep.procent.toFixed(1) + '%';

        // Zmiana koloru paska postępu
        if (postep.procent >= 100) {
            progressBar.style.background = 'linear-gradient(90deg, #10b981, #059669)';
        } else if (postep.procent >= 75) {
            progressBar.style.background = 'linear-gradient(90deg, var(--taxi-yellow), #f59e0b)';
        } else {
            progressBar.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
        }
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

// PWA Installation
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;

    // Pokaż banner instalacji jeśli użytkownik nie odrzucił go wcześniej
    if (!localStorage.getItem('pwa-banner-dismissed')) {
        const banner = document.getElementById('install-banner');
        if (banner) {
            banner.style.display = 'block';
        }
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
            const banner = document.getElementById('install-banner');
            if (banner) {
                banner.style.display = 'none';
            }
        });
    }
}

function zamknijBanner() {
    const banner = document.getElementById('install-banner');
    if (banner) {
        banner.style.display = 'none';
    }
    localStorage.setItem('pwa-banner-dismissed', 'true');
}

// Tryb ciemny
function przełączTryb() {
    const body = document.body;
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    body.classList.toggle('dark-mode');

    if (body.classList.contains('dark-mode')) {
        if (icon) icon.className = 'bi bi-sun';
        if (text) text.textContent = 'Tryb jasny';
        localStorage.setItem('theme', 'dark');
    } else {
        if (icon) icon.className = 'bi bi-moon-stars';
        if (text) text.textContent = 'Tryb ciemny';
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

    // Wczytaj cele (tylko jeśli jesteśmy na stronie z celami)
    if (document.getElementById('cel-dzienny')) {
        await wczytajCele();
    }

    // Wczytaj średnią dnia (tylko jeśli element istnieje)
    const sredniaDniaElement = document.getElementById('srednia-dnia');
    if (sredniaDniaElement) {
        try {
            const response = await fetch('/srednia_dnia');
            const dane = await response.json();
            if (dane.srednia_dnia !== 'Brak danych') {
                sredniaDniaElement.textContent = dane.srednia_dnia + ' zł/h';
            }
        } catch (error) {
            console.log('Nie udało się wczytać średniej dnia');
        }
    }
});