
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

// Wczytanie średniej dnia przy starcie
window.addEventListener('load', async function() {
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
