
from flask import Flask, render_template, request, jsonify
import datetime

app = Flask(__name__)
PLIK = "kursy.txt"

def zapisz_do_pliku(dane):
    with open(PLIK, "a", encoding="utf-8") as plik:
        plik.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        for klucz, wartosc in dane.items():
            plik.write(f"{klucz}: {wartosc}\n")
        plik.write("-" * 40 + "\n")

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

    return {
        "dystans_calkowity": f"{dystans_calkowity:.2f}",
        "czas_calkowity_h": f"{czas_calkowity_h:.2f}",
        "koszt_paliwa": f"{koszt_paliwa:.2f}",
        "zarobek_dla_kierowcy": f"{zarobek_dla_kierowcy:.2f}",
        "zysk_netto": f"{zysk_netto:.2f}",
        "stawka_godzinowa": f"{stawka_godzinowa:.2f}",
        "ocena": ocena,
        "ocena_klasa": ocena_klasa,
        "srednia_dnia": f"{srednia_dnia:.2f}" if srednia_dnia else "Brak danych"
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/oblicz', methods=['POST'])
def oblicz():
    dane = request.json
    wynik = oblicz_oplacalnosc(dane)
    return jsonify(wynik)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
