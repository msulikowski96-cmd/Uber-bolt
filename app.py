
from flask import Flask, render_template, request, jsonify, session
import datetime

app = Flask(__name__)
app.secret_key = 'taxi-calculator-secret-key-2025'
PLIK = "kursy.txt"
CELE_PLIK = "cele.txt"

def zapisz_do_pliku(dane):
    with open(PLIK, "a", encoding="utf-8") as plik:
        plik.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        for klucz, wartosc in dane.items():
            plik.write(f"{klucz}: {wartosc}\n")
        plik.write("-" * 40 + "\n")

def wczytaj_cele():
    """Wczytuje cele użytkownika z pliku."""
    try:
        with open(CELE_PLIK, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
            cele = {}
            for linia in linie:
                if ":" in linia:
                    klucz, wartosc = linia.strip().split(":", 1)
                    cele[klucz] = wartosc.strip()
            return cele
    except FileNotFoundError:
        return {"cel_dzienny": "300", "min_stawka": "30"}

def zapisz_cele(cele):
    """Zapisuje cele użytkownika do pliku."""
    with open(CELE_PLIK, "w", encoding="utf-8") as plik:
        for klucz, wartosc in cele.items():
            plik.write(f"{klucz}:{wartosc}\n")

def oblicz_postep_celu():
    """Oblicza postęp do dziennego celu."""
    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    cele = wczytaj_cele()
    cel_dzienny = float(cele.get("cel_dzienny", 300))
    
    try:
        with open(PLIK, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return {"postep": 0, "cel": cel_dzienny, "procent": 0, "pozostalo": cel_dzienny}
    
    suma_zysku = 0
    dzien = None
    
    for linia in linie:
        if linia.startswith("["):
            data = linia[1:11]
            dzien = data
        elif "Zysk netto:" in linia and dzien == dzisiaj:
            wartosc = float(linia.strip().split(":")[1].replace("zł", "").strip())
            suma_zysku += wartosc
    
    procent = min((suma_zysku / cel_dzienny) * 100, 100) if cel_dzienny > 0 else 0
    pozostalo = max(cel_dzienny - suma_zysku, 0)
    
    return {
        "postep": suma_zysku,
        "cel": cel_dzienny,
        "procent": procent,
        "pozostalo": pozostalo
    }

def aktualizuj_srednia_dnia():
    """Aktualizuje średnią stawkę godzinową dla dzisiejszego dnia."""
    try:
        with open(PLIK, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return None

    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    stawki = []
    nowe_linie = []

    for linia in linie:
        if linia.startswith("📊 Podsumowanie dnia") and dzisiaj in linia:
            continue
        nowe_linie.append(linia)
        if linia.startswith("["):
            data = linia[1:11]
            dzien = data
        elif "Stawka godzinowa:" in linia and dzien == dzisiaj:
            wartosc = float(linia.strip().split(":")[1].replace("zł/h", "").strip())
            stawki.append(wartosc)

    if stawki:
        srednia = sum(stawki) / len(stawki)
        nowe_linie.append(f"\n📊 Podsumowanie dnia {dzisiaj} - średnia stawka godzinowa: {srednia:.2f} zł/h\n")
        nowe_linie.append("=" * 40 + "\n")

        with open(PLIK, "w", encoding="utf-8") as plik:
            plik.writelines(nowe_linie)
        return srednia
    return None

def oblicz_oplacalnosc(dane):
    dystans_dojazdu = float(dane['dystans_dojazdu'])
    czas_dojazdu = float(dane['czas_dojazdu'])
    dystans_kursu = float(dane['dystans_kursu'])
    czas_kursu = float(dane['czas_kursu'])
    kwota = float(dane['kwota'])
    procent_dla_kierowcy = float(dane['procent_dla_kierowcy'])
    spalanie = float(dane['spalanie'])
    cena_paliwa = float(dane['cena_paliwa'])

    dystans_calkowity = dystans_dojazdu + dystans_kursu
    czas_calkowity_h = (czas_dojazdu + czas_kursu) / 60
    koszt_paliwa = (dystans_calkowity * spalanie / 100) * cena_paliwa
    zarobek_dla_kierowcy = kwota * (procent_dla_kierowcy / 100)
    zysk_netto = zarobek_dla_kierowcy - koszt_paliwa
    stawka_godzinowa = zysk_netto / czas_calkowity_h if czas_calkowity_h > 0 else 0

    if stawka_godzinowa >= 50:
        ocena = "💰 Kurs bardzo opłacalny!"
        ocena_klasa = "success"
    elif stawka_godzinowa >= 30:
        ocena = "👍 Kurs opłacalny."
        ocena_klasa = "info"
    elif stawka_godzinowa >= 20:
        ocena = "😐 Kurs średnio opłacalny."
        ocena_klasa = "warning"
    else:
        ocena = "❌ Kurs nieopłacalny."
        ocena_klasa = "danger"

    dane_do_zapisu = {
        "Dystans dojazdu (km)": f"{dystans_dojazdu:.2f}",
        "Czas dojazdu (min)": f"{czas_dojazdu:.0f}",
        "Dystans z klientem (km)": f"{dystans_kursu:.2f}",
        "Czas kursu (min)": f"{czas_kursu:.0f}",
        "Kwota (z napiwkiem)": f"{kwota:.2f} zł",
        "Procent dla kierowcy": f"{procent_dla_kierowcy:.0f}%",
        "Koszt paliwa": f"{koszt_paliwa:.2f} zł",
        "Zysk netto": f"{zysk_netto:.2f} zł",
        "Stawka godzinowa": f"{stawka_godzinowa:.2f} zł/h",
        "Ocena": ocena
    }

    zapisz_do_pliku(dane_do_zapisu)
    srednia_dnia = aktualizuj_srednia_dnia()
    
    # Sprawdzenie celów i powiadomienia
    cele = wczytaj_cele()
    min_stawka = float(cele.get("min_stawka", 30))
    postep = oblicz_postep_celu()
    
    powiadomienia = []
    
    # Alert o niskiej stawce
    if stawka_godzinowa < min_stawka:
        powiadomienia.append({
            "typ": "warning",
            "tekst": f"⚠️ Stawka godzinowa ({stawka_godzinowa:.2f} zł/h) poniżej minimalnej ({min_stawka:.2f} zł/h)!"
        })
    
    # Gratulacje za osiągnięcie celu
    if postep["procent"] >= 100:
        powiadomienia.append({
            "typ": "success",
            "tekst": f"🎉 Gratulacje! Osiągnąłeś dzienny cel ({postep['cel']:.2f} zł)!"
        })
    elif postep["procent"] >= 75:
        powiadomienia.append({
            "typ": "info",
            "tekst": f"💪 Blisko celu! Pozostało tylko {postep['pozostalo']:.2f} zł do dziennego celu."
        })

    return {
        "dystans_calkowity": f"{dystans_calkowity:.2f}",
        "czas_calkowity_h": f"{czas_calkowity_h:.2f}",
        "koszt_paliwa": f"{koszt_paliwa:.2f}",
        "zarobek_dla_kierowcy": f"{zarobek_dla_kierowcy:.2f}",
        "zysk_netto": f"{zysk_netto:.2f}",
        "stawka_godzinowa": f"{stawka_godzinowa:.2f}",
        "ocena": ocena,
        "ocena_klasa": ocena_klasa,
        "srednia_dnia": f"{srednia_dnia:.2f}" if srednia_dnia else "Brak danych",
        "postep": postep,
        "powiadomienia": powiadomienia
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/static/service-worker.js')
def service_worker():
    from flask import send_from_directory
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/oblicz', methods=['POST'])
def oblicz():
    dane = request.json
    wynik = oblicz_oplacalnosc(dane)
    return jsonify(wynik)

@app.route('/statystyki')
def statystyki():
    return render_template('statystyki.html')

@app.route('/cele', methods=['GET', 'POST'])
def cele():
    if request.method == 'POST':
        dane = request.json
        zapisz_cele(dane)
        return jsonify({"sukces": True})
    else:
        cele = wczytaj_cele()
        postep = oblicz_postep_celu()
        return jsonify({"cele": cele, "postep": postep})

@app.route('/srednia_dnia')
def srednia_dnia():
    """Endpoint do pobierania średniej stawki godzinowej z dzisiaj."""
    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        with open(PLIK, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({"srednia_dnia": "Brak danych"})
    
    stawki = []
    dzien = None
    
    for linia in linie:
        if linia.startswith("["):
            data = linia[1:11]
            dzien = data
        elif "Stawka godzinowa:" in linia and dzien == dzisiaj:
            wartosc = float(linia.strip().split(":")[1].replace("zł/h", "").strip())
            stawki.append(wartosc)
    
    if stawki:
        srednia = sum(stawki) / len(stawki)
        return jsonify({"srednia_dnia": f"{srednia:.2f}"})
    else:
        return jsonify({"srednia_dnia": "Brak danych"})

@app.route('/dane_statystyk')
def dane_statystyk():
    import plotly.graph_objects as go
    import plotly.utils
    import json
    
    try:
        with open(PLIK, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({"error": "Brak danych"})
    
    kursy = []
    kurs = {}
    
    for linia in linie:
        if linia.startswith("["):
            if kurs:
                kursy.append(kurs)
            kurs = {"data": linia[1:20]}
        elif "Stawka godzinowa:" in linia:
            kurs["stawka"] = float(linia.strip().split(":")[1].replace("zł/h", "").strip())
        elif "Zysk netto:" in linia:
            kurs["zysk"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
        elif "Kwota (z napiwkiem):" in linia:
            kurs["kwota"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
    
    if kurs and "stawka" in kurs:
        kursy.append(kurs)
    
    if not kursy:
        return jsonify({"error": "Brak danych"})
    
    # Wykres stawki godzinowej w czasie
    daty = [k["data"] for k in kursy if "stawka" in k]
    stawki = [k["stawka"] for k in kursy if "stawka" in k]
    
    fig_stawka = go.Figure()
    fig_stawka.add_trace(go.Scatter(
        x=daty, 
        y=stawki,
        mode='lines+markers',
        name='Stawka godzinowa',
        line=dict(color='#667eea', width=3),
        marker=dict(size=8)
    ))
    fig_stawka.update_layout(
        title='Stawka godzinowa w czasie',
        xaxis_title='Data i czas',
        yaxis_title='Stawka (zł/h)',
        template='plotly_white',
        height=400
    )
    
    # Wykres zysków
    zyski = [k["zysk"] for k in kursy if "zysk" in k]
    
    fig_zysk = go.Figure()
    fig_zysk.add_trace(go.Bar(
        x=daty,
        y=zyski,
        name='Zysk netto',
        marker=dict(color='#10b981')
    ))
    fig_zysk.update_layout(
        title='Zysk netto z kursów',
        xaxis_title='Data i czas',
        yaxis_title='Zysk (zł)',
        template='plotly_white',
        height=400
    )
    
    # Statystyki godzinowe
    from collections import defaultdict
    stawki_po_godzinach = defaultdict(list)
    
    for k in kursy:
        if "data" in k and "stawka" in k:
            godzina = int(k["data"][11:13])
            stawki_po_godzinach[godzina].append(k["stawka"])
    
    godziny = sorted(stawki_po_godzinach.keys())
    srednie_stawki = [sum(stawki_po_godzinach[g])/len(stawki_po_godzinach[g]) for g in godziny]
    
    fig_godziny = go.Figure()
    fig_godziny.add_trace(go.Bar(
        x=[f"{g:02d}:00" for g in godziny],
        y=srednie_stawki,
        name='Średnia stawka',
        marker=dict(color=srednie_stawki, colorscale='RdYlGn', showscale=True)
    ))
    fig_godziny.update_layout(
        title='Średnia stawka godzinowa według godzin dnia',
        xaxis_title='Godzina',
        yaxis_title='Średnia stawka (zł/h)',
        template='plotly_white',
        height=400
    )
    
    # Statystyki ogólne
    suma_zyskow = sum(zyski)
    srednia_stawka = sum(stawki) / len(stawki) if stawki else 0
    najlepsza_stawka = max(stawki) if stawki else 0
    najgorsza_stawka = min(stawki) if stawki else 0
    najlepsza_godzina = godziny[srednie_stawki.index(max(srednie_stawki))] if srednie_stawki else 0
    
    return jsonify({
        "wykres_stawka": json.loads(json.dumps(fig_stawka, cls=plotly.utils.PlotlyJSONEncoder)),
        "wykres_zysk": json.loads(json.dumps(fig_zysk, cls=plotly.utils.PlotlyJSONEncoder)),
        "wykres_godziny": json.loads(json.dumps(fig_godziny, cls=plotly.utils.PlotlyJSONEncoder)),
        "statystyki": {
            "suma_zyskow": f"{suma_zyskow:.2f}",
            "srednia_stawka": f"{srednia_stawka:.2f}",
            "najlepsza_stawka": f"{najlepsza_stawka:.2f}",
            "najgorsza_stawka": f"{najgorsza_stawka:.2f}",
            "liczba_kursow": len(kursy),
            "najlepsza_godzina": f"{najlepsza_godzina:02d}:00"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
