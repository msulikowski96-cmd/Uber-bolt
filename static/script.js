
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
        div.innerHTML = `<strong>${powiadomienie.tekst}</strong>`;
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

// Wczytanie danych przy starcie
window.addEventListener('load', async function() {
    // Wczytaj cele
    await wczytajCele();
    
    // Wczytaj średnią dnia
    try {
        const response = await fetch('/oblicz', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                dystans_dojazdu: 0,
                czas_dojazdu: 1,
                dystans_kursu: 0,
                czas_kursu: 1,
                kwota: 0,
                procent_dla_kierowcy: 100,
                spalanie: 5,
                cena_paliwa: 6.5
            })
        });
        const wynik = await response.json();
        if (wynik.srednia_dnia !== 'Brak danych') {
            document.getElementById('srednia-dnia').textContent = wynik.srednia_dnia + ' zł/h';
        }
    } catch (error) {
        console.log('Nie udało się wczytać średniej dnia');
    }
});
