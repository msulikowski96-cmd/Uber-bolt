from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from urllib.parse import urlparse, urljoin
import datetime
import os
from database import db, User, get_user_folder, init_db
from forms import LoginForm, RegistrationForm

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
if not app.secret_key:
    raise ValueError("SESSION_SECRET environment variable must be set")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Konfiguracja Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Zaloguj się, aby uzyskać dostęp do tej strony.'
login_manager.login_message_category = 'info'

# Inicjalizacja bazy danych
init_db(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def is_safe_url(target):
    """Validate that a redirect URL is safe (relative path only)"""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_user_file(filename):
    """Zwraca ścieżkę do pliku użytkownika"""
    user_folder = get_user_folder(current_user.id)
    return f'{user_folder}/{filename}'

def zapisz_do_pliku(dane):
    plik_path = get_user_file('kursy.txt')
    with open(plik_path, "a", encoding="utf-8") as plik:
        plik.write(f"\n[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        for klucz, wartosc in dane.items():
            plik.write(f"{klucz}: {wartosc}\n")
        plik.write("-" * 40 + "\n")

def wczytaj_cele():
    """Wczytuje cele użytkownika z pliku."""
    try:
        plik_path = get_user_file('cele.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
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
    plik_path = get_user_file('cele.txt')
    with open(plik_path, "w", encoding="utf-8") as plik:
        for klucz, wartosc in cele.items():
            plik.write(f"{klucz}:{wartosc}\n")

def oblicz_postep_celu():
    """Oblicza postęp do dziennego celu."""
    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    cele = wczytaj_cele()
    cel_dzienny = float(cele.get("cel_dzienny", 300))
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
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
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return None

    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    stawki = []
    nowe_linie = []
    dzien = None

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

        with open(plik_path, "w", encoding="utf-8") as plik:
            plik.writelines(nowe_linie)
        return srednia
    return None

def wczytaj_historie_kursow():
    """Wczytuje pełną historię kursów z pliku."""
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return []
    
    kursy = []
    kurs = {}
    data_czas = None
    
    for linia in linie:
        linia = linia.strip()
        
        # Pomijaj linie podsumowań i separatorów
        if linia.startswith("📊") or linia.startswith("=") or not linia:
            continue
            
        # Znacznik czasu
        if linia.startswith("[") and linia.endswith("]"):
            # Zapisz poprzedni kurs jeśli istnieje
            if kurs and data_czas:
                kurs['data_czas'] = data_czas
                kursy.append(kurs)
            # Rozpocznij nowy kurs
            data_czas = linia[1:-1]
            kurs = {}
        # Separator między kursami
        elif linia.startswith("-"):
            if kurs and data_czas:
                kurs['data_czas'] = data_czas
                kursy.append(kurs)
                kurs = {}
                data_czas = None
        # Parsuj dane kursu
        elif ":" in linia:
            klucz, wartosc = linia.split(":", 1)
            klucz = klucz.strip()
            wartosc = wartosc.strip()
            kurs[klucz] = wartosc
    
    # Dodaj ostatni kurs jeśli istnieje
    if kurs and data_czas:
        kurs['data_czas'] = data_czas
        kursy.append(kurs)
    
    # Odwróć listę, aby najnowsze kursy były pierwsze
    kursy.reverse()
    
    return kursy

def oblicz_oplacalnosc(dane):
    dystans_dojazdu = float(dane['dystans_dojazdu'])
    czas_dojazdu = float(dane['czas_dojazdu'])
    dystans_kursu = float(dane['dystans_kursu'])
    czas_kursu = float(dane['czas_kursu'])
    kwota = float(dane['kwota'])
    procent_dla_kierowcy = float(dane['procent_dla_kierowcy'])
    spalanie = float(dane['spalanie'])
    cena_paliwa = float(dane['cena_paliwa'])
    platforma = dane.get('platforma', 'Nieznana')

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
        "Platforma": platforma,
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
    
    cele = wczytaj_cele()
    min_stawka = float(cele.get("min_stawka", 30))
    postep = oblicz_postep_celu()
    
    powiadomienia = []
    
    if stawka_godzinowa < min_stawka:
        powiadomienia.append({
            "typ": "warning",
            "tekst": f"⚠️ Stawka godzinowa ({stawka_godzinowa:.2f} zł/h) poniżej minimalnej ({min_stawka:.2f} zł/h)!"
        })
    
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

# Routes autentykacji
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.verify_password(form.email.data, form.password.data)
        if user:
            login_user(user)
            flash('Zalogowano pomyślnie!', 'success')
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Nieprawidłowy email lub hasło.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User.create(form.email.data, form.password.data)
        if user:
            flash('Konto utworzone pomyślnie! Możesz się teraz zalogować.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Ten email jest już zarejestrowany.', 'error')
    
    return render_template('register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Wylogowano pomyślnie.', 'success')
    return redirect(url_for('login'))

# Routes aplikacji
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/static/service-worker.js')
def service_worker():
    from flask import send_from_directory
    return send_from_directory('static', 'service-worker.js', mimetype='application/javascript')

@app.route('/oblicz', methods=['POST'])
@login_required
def oblicz():
    dane = request.json
    wynik = oblicz_oplacalnosc(dane)
    return jsonify(wynik)

@app.route('/statystyki')
@login_required
def statystyki():
    return render_template('statystyki.html')

@app.route('/platformy')
@login_required
def platformy():
    return render_template('platformy.html')

@app.route('/raporty')
@login_required
def raporty():
    return render_template('raporty.html')

@app.route('/historia')
@login_required
def historia():
    return render_template('historia.html')

@app.route('/api/historia')
@login_required
def api_historia():
    kursy = wczytaj_historie_kursow()
    return jsonify(kursy)

@app.route('/cele', methods=['GET', 'POST'])
@login_required
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
@login_required
def srednia_dnia():
    """Endpoint do pobierania średniej stawki godzinowej z dzisiaj."""
    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
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
@login_required
def dane_statystyk():
    import plotly.graph_objects as go
    import plotly.utils
    import json
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
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

@app.route('/statystyki_platform')
@login_required
def statystyki_platform():
    """Endpoint do porównania platform."""
    import plotly.graph_objects as go
    import plotly.utils
    import json
    from collections import defaultdict
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
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
        elif "Platforma:" in linia:
            kurs["platforma"] = linia.strip().split(":", 1)[1].strip()
        elif "Stawka godzinowa:" in linia:
            kurs["stawka"] = float(linia.strip().split(":")[1].replace("zł/h", "").strip())
        elif "Zysk netto:" in linia:
            kurs["zysk"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
    
    if kurs and "stawka" in kurs:
        kursy.append(kurs)
    
    if not kursy:
        return jsonify({"error": "Brak danych"})
    
    dane_platform = defaultdict(lambda: {"stawki": [], "zyski": [], "liczba": 0})
    
    for kurs in kursy:
        platforma = kurs.get("platforma", "Nieznana")
        if "stawka" in kurs:
            dane_platform[platforma]["stawki"].append(kurs["stawka"])
        if "zysk" in kurs:
            dane_platform[platforma]["zyski"].append(kurs["zysk"])
        dane_platform[platforma]["liczba"] += 1
    
    platformy = []
    srednie_stawki = []
    suma_zyskow_platform = []
    liczba_kursow_platform = []
    
    for platforma, dane in dane_platform.items():
        platformy.append(platforma)
        srednia = sum(dane["stawki"]) / len(dane["stawki"]) if dane["stawki"] else 0
        srednie_stawki.append(srednia)
        suma_zyskow = sum(dane["zyski"])
        suma_zyskow_platform.append(suma_zyskow)
        liczba_kursow_platform.append(dane["liczba"])
    
    fig_stawki = go.Figure()
    fig_stawki.add_trace(go.Bar(
        x=platformy,
        y=srednie_stawki,
        name='Średnia stawka',
        marker=dict(color=srednie_stawki, colorscale='RdYlGn', showscale=True),
        text=[f"{s:.2f} zł/h" for s in srednie_stawki],
        textposition='auto'
    ))
    fig_stawki.update_layout(
        title='Średnia stawka godzinowa według platform',
        xaxis_title='Platforma',
        yaxis_title='Średnia stawka (zł/h)',
        template='plotly_white',
        height=400
    )
    
    fig_zyski = go.Figure()
    fig_zyski.add_trace(go.Bar(
        x=platformy,
        y=suma_zyskow_platform,
        name='Suma zysków',
        marker=dict(color='#10b981'),
        text=[f"{z:.2f} zł" for z in suma_zyskow_platform],
        textposition='auto'
    ))
    fig_zyski.update_layout(
        title='Suma zysków według platform',
        xaxis_title='Platforma',
        yaxis_title='Suma zysków (zł)',
        template='plotly_white',
        height=400
    )
    
    fig_liczba = go.Figure()
    fig_liczba.add_trace(go.Bar(
        x=platformy,
        y=liczba_kursow_platform,
        name='Liczba kursów',
        marker=dict(color='#667eea'),
        text=liczba_kursow_platform,
        textposition='auto'
    ))
    fig_liczba.update_layout(
        title='Liczba kursów według platform',
        xaxis_title='Platforma',
        yaxis_title='Liczba kursów',
        template='plotly_white',
        height=400
    )
    
    if srednie_stawki:
        idx_najlepsza = srednie_stawki.index(max(srednie_stawki))
        najlepsza_platforma = platformy[idx_najlepsza]
        najlepsza_stawka = srednie_stawki[idx_najlepsza]
    else:
        najlepsza_platforma = "Brak danych"
        najlepsza_stawka = 0
    
    return jsonify({
        "wykres_stawki": json.loads(json.dumps(fig_stawki, cls=plotly.utils.PlotlyJSONEncoder)),
        "wykres_zyski": json.loads(json.dumps(fig_zyski, cls=plotly.utils.PlotlyJSONEncoder)),
        "wykres_liczba": json.loads(json.dumps(fig_liczba, cls=plotly.utils.PlotlyJSONEncoder)),
        "najlepsza_platforma": najlepsza_platforma,
        "najlepsza_stawka": f"{najlepsza_stawka:.2f}"
    })

@app.route('/api/raport')
@login_required
def api_raport():
    """Generuje raport za wybrany okres"""
    typ = request.args.get('typ', 'miesiac')
    data = request.args.get('data', datetime.datetime.now().strftime('%Y-%m'))
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({
            "zarobki_brutto": "0.00",
            "zarobki_netto": "0.00",
            "liczba_kursow": 0,
            "przejechane_km": "0.00"
        })
    
    kursy = []
    kurs = {}
    
    for linia in linie:
        if linia.startswith("["):
            if kurs:
                kursy.append(kurs)
            kurs = {"data": linia[1:20]}
        elif "Kwota (z napiwkiem):" in linia:
            kurs["kwota"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
        elif "Zysk netto:" in linia:
            kurs["zysk"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
        elif "Dystans dojazdu (km):" in linia:
            kurs["dystans_dojazd"] = float(linia.strip().split(":")[1].strip())
        elif "Dystans z klientem (km):" in linia:
            kurs["dystans_kurs"] = float(linia.strip().split(":")[1].strip())
    
    if kurs and "kwota" in kurs:
        kursy.append(kurs)
    
    kursy_okresu = []
    for k in kursy:
        if typ == 'miesiac' and k["data"][:7] == data:
            kursy_okresu.append(k)
        elif typ == 'tydzien':
            pass
    
    zarobki_brutto = sum(k.get("kwota", 0) for k in kursy_okresu)
    zarobki_netto = sum(k.get("zysk", 0) for k in kursy_okresu)
    liczba_kursow = len(kursy_okresu)
    przejechane_km = sum(k.get("dystans_dojazd", 0) + k.get("dystans_kurs", 0) for k in kursy_okresu)
    
    return jsonify({
        "zarobki_brutto": f"{zarobki_brutto:.2f}",
        "zarobki_netto": f"{zarobki_netto:.2f}",
        "liczba_kursow": liczba_kursow,
        "przejechane_km": f"{przejechane_km:.2f}"
    })

@app.route('/api/prognoza')
@login_required
def api_prognoza():
    """Prognozuje zarobki na podstawie historii"""
    import plotly.graph_objects as go
    import plotly.utils
    import json
    from datetime import timedelta
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({
            "dni_historii": 0,
            "prognoza_miesiac": "0.00",
            "srednia_dzienna": "0.00",
            "trend": "brak danych",
            "wykres_data": [],
            "wykres_layout": {}
        })
    
    kursy = []
    kurs = {}
    
    for linia in linie:
        if linia.startswith("["):
            if kurs:
                kursy.append(kurs)
            kurs = {"data": linia[1:10], "data_pelna": linia[1:20]}
        elif "Zysk netto:" in linia:
            kurs["zysk"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
    
    if kurs and "zysk" in kurs:
        kursy.append(kurs)
    
    zarobki_dzienne = {}
    for k in kursy:
        if "data" in k and "zysk" in k:
            data = k["data"]
            if data not in zarobki_dzienne:
                zarobki_dzienne[data] = 0
            zarobki_dzienne[data] += k["zysk"]
    
    ostatnie_30_dni = sorted(zarobki_dzienne.items())[-30:]
    
    if ostatnie_30_dni:
        srednia_dzienna = sum(z for d, z in ostatnie_30_dni) / len(ostatnie_30_dni)
        dzisiaj = datetime.datetime.now()
        dni_w_miesiacu = (datetime.datetime(dzisiaj.year, dzisiaj.month + 1 if dzisiaj.month < 12 else 1, 1) - datetime.datetime(dzisiaj.year, dzisiaj.month, 1)).days
        prognoza_miesiac = srednia_dzienna * dni_w_miesiacu
        
        pierwsze_5 = sum(z for d, z in ostatnie_30_dni[:5]) / 5 if len(ostatnie_30_dni) >= 5 else srednia_dzienna
        ostatnie_5 = sum(z for d, z in ostatnie_30_dni[-5:]) / 5 if len(ostatnie_30_dni) >= 5 else srednia_dzienna
        
        if ostatnie_5 > pierwsze_5 * 1.1:
            trend = "rosnący 📈"
        elif ostatnie_5 < pierwsze_5 * 0.9:
            trend = "malejący 📉"
        else:
            trend = "stabilny ➡️"
        
        daty = [d for d, z in ostatnie_30_dni]
        zarobki = [z for d, z in ostatnie_30_dni]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daty,
            y=zarobki,
            mode='lines+markers',
            name='Dzienny zysk',
            line=dict(color='#667eea', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=daty,
            y=[srednia_dzienna] * len(daty),
            mode='lines',
            name='Średnia',
            line=dict(color='#10b981', width=2, dash='dash')
        ))
        fig.update_layout(
            title='Historia zarobków dziennych',
            xaxis_title='Data',
            yaxis_title='Zysk (zł)',
            template='plotly_white',
            height=300
        )
        
        return jsonify({
            "dni_historii": len(ostatnie_30_dni),
            "prognoza_miesiac": f"{prognoza_miesiac:.2f}",
            "srednia_dzienna": f"{srednia_dzienna:.2f}",
            "trend": trend,
            "wykres_data": json.loads(json.dumps(fig.data, cls=plotly.utils.PlotlyJSONEncoder)),
            "wykres_layout": json.loads(json.dumps(fig.layout, cls=plotly.utils.PlotlyJSONEncoder))
        })
    else:
        return jsonify({
            "dni_historii": 0,
            "prognoza_miesiac": "0.00",
            "srednia_dzienna": "0.00",
            "trend": "brak danych",
            "wykres_data": [],
            "wykres_layout": {}
        })

@app.route('/api/kilometry')
@login_required
def api_kilometry():
    """Zwraca statystyki kilometrów"""
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({
            "calkowite": "0",
            "miesiac": "0",
            "srednia_dzien": "0",
            "koszt_km": "0.00"
        })
    
    kursy = []
    kurs = {}
    
    for linia in linie:
        if linia.startswith("["):
            if kurs:
                kursy.append(kurs)
            kurs = {"data": linia[1:10]}
        elif "Dystans dojazdu (km):" in linia:
            kurs["dystans_dojazd"] = float(linia.strip().split(":")[1].strip())
        elif "Dystans z klientem (km):" in linia:
            kurs["dystans_kurs"] = float(linia.strip().split(":")[1].strip())
        elif "Koszt paliwa:" in linia:
            kurs["koszt_paliwa"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
    
    if kurs:
        kursy.append(kurs)
    
    calkowity_dystans = 0
    calkowity_koszt = 0
    
    dzisiaj = datetime.datetime.now()
    miesiac_obecny = dzisiaj.strftime("%Y-%m")
    dystans_miesiac = 0
    dni_w_miesiacu = set()
    
    for k in kursy:
        dystans = k.get("dystans_dojazd", 0) + k.get("dystans_kurs", 0)
        calkowity_dystans += dystans
        calkowity_koszt += k.get("koszt_paliwa", 0)
        
        if k.get("data", "")[:7] == miesiac_obecny:
            dystans_miesiac += dystans
            dni_w_miesiacu.add(k.get("data"))
    
    koszt_na_km = calkowity_koszt / calkowity_dystans if calkowity_dystans > 0 else 0
    srednia_dzien = dystans_miesiac / len(dni_w_miesiacu) if dni_w_miesiacu else 0
    
    return jsonify({
        "calkowite": f"{calkowity_dystans:.0f}",
        "miesiac": f"{dystans_miesiac:.0f}",
        "srednia_dzien": f"{srednia_dzien:.0f}",
        "koszt_km": f"{koszt_na_km:.2f}"
    })

@app.route('/api/heatmap_rentownosci')
@login_required
def api_heatmap_rentownosci():
    """Generuje heatmapę rentowności według dnia tygodnia i godziny"""
    import plotly.graph_objects as go
    import plotly.utils
    import json
    from collections import defaultdict
    
    try:
        plik_path = get_user_file('kursy.txt')
        with open(plik_path, "r", encoding="utf-8") as plik:
            linie = plik.readlines()
    except FileNotFoundError:
        return jsonify({"error": "Brak danych"})
    
    kursy = []
    kurs = {}
    
    for linia in linie:
        if linia.startswith("["):
            if kurs:
                kursy.append(kurs)
            kurs = {"data_pelna": linia[1:20]}
        elif "Zysk netto:" in linia:
            kurs["zysk"] = float(linia.strip().split(":")[1].replace("zł", "").strip())
    
    if kurs and "zysk" in kurs:
        kursy.append(kurs)
    
    if not kursy:
        return jsonify({"error": "Brak danych"})
    
    rentownosc = defaultdict(lambda: defaultdict(list))
    
    dni_tygodnia_pl = ['Poniedziałek', 'Wtorek', 'Środa', 'Czwartek', 'Piątek', 'Sobota', 'Niedziela']
    
    for k in kursy:
        if "data_pelna" in k and "zysk" in k:
            try:
                data_obj = datetime.datetime.strptime(k["data_pelna"], "%Y-%m-%d %H:%M:%S")
                dzien_tygodnia = data_obj.weekday()
                godzina = data_obj.hour
                rentownosc[dzien_tygodnia][godzina].append(k["zysk"])
            except:
                continue
    
    godziny = list(range(24))
    macierz_rentownosci = []
    
    for dzien in range(7):
        wiersz = []
        for godzina in godziny:
            if rentownosc[dzien][godzina]:
                srednia = sum(rentownosc[dzien][godzina]) / len(rentownosc[dzien][godzina])
                wiersz.append(srednia)
            else:
                wiersz.append(None)
        macierz_rentownosci.append(wiersz)
    
    fig = go.Figure(data=go.Heatmap(
        z=macierz_rentownosci,
        x=[f"{g:02d}:00" for g in godziny],
        y=dni_tygodnia_pl,
        colorscale='RdYlGn',
        hoverongaps=False,
        hovertemplate='%{y}<br>%{x}<br>Średni zysk: %{z:.2f} zł<extra></extra>'
    ))
    
    fig.update_layout(
        title='Rentowność według dnia tygodnia i godziny',
        xaxis_title='Godzina',
        yaxis_title='Dzień tygodnia',
        template='plotly_white',
        height=500
    )
    
    najlepsze_sloty = []
    for dzien in range(7):
        for godzina in godziny:
            if rentownosc[dzien][godzina]:
                srednia = sum(rentownosc[dzien][godzina]) / len(rentownosc[dzien][godzina])
                liczba_kursow = len(rentownosc[dzien][godzina])
                najlepsze_sloty.append({
                    'dzien': dni_tygodnia_pl[dzien],
                    'godzina': f"{godzina:02d}:00",
                    'sredni_zysk': srednia,
                    'liczba_kursow': liczba_kursow
                })
    
    najlepsze_sloty.sort(key=lambda x: x['sredni_zysk'], reverse=True)
    top_3 = najlepsze_sloty[:3]
    
    return jsonify({
        "wykres": json.loads(json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)),
        "top_sloty": top_3
    })

@app.route('/ai-asystent')
@login_required
def ai_asystent():
    """Strona AI Asystenta"""
    return render_template('ai_asystent.html')

@app.route('/api/ai-analiza', methods=['POST'])
@login_required
def ai_analiza():
    """Endpoint do analizy danych przez AI"""
    import json
    import requests
    
    data = request.json
    typ = data.get('typ')
    pytanie = data.get('pytanie', '')
    
    # Pobierz dane kursów użytkownika
    kursy = wczytaj_historie_kursow()
    
    if not kursy:
        return jsonify({
            'analiza': 'Nie masz jeszcze żadnych zapisanych kursów. Zacznij dodawać kursy w kalkulatorze, aby AI mogło przeanalizować Twoje dane.'
        })
    
    # Przygotuj podsumowanie danych dla AI
    ile_kursow = len(kursy)
    platformy = {}
    suma_zysk = 0
    suma_stawka = 0
    stawki_lista = []
    
    for kurs in kursy:
        platforma = kurs.get('Platforma', 'Inne')
        if platforma not in platformy:
            platformy[platforma] = {'liczba': 0, 'zysk': 0, 'stawki': []}
        platformy[platforma]['liczba'] += 1
        
        zysk_str = kurs.get('Zysk netto', '0').replace('zł', '').strip()
        stawka_str = kurs.get('Stawka godzinowa', '0').replace('zł/h', '').strip()
        
        try:
            zysk = float(zysk_str)
            suma_zysk += zysk
            platformy[platforma]['zysk'] += zysk
        except:
            pass
        
        try:
            stawka = float(stawka_str)
            suma_stawka += stawka
            stawki_lista.append(stawka)
            platformy[platforma]['stawki'].append(stawka)
        except:
            pass
    
    srednia_stawka = suma_stawka / len(stawki_lista) if stawki_lista else 0
    
    # Analiza czasowa
    from collections import defaultdict
    import datetime as dt
    
    zarobki_dzien_tygodnia = defaultdict(list)
    zarobki_godzina = defaultdict(list)
    
    for kurs in kursy:
        try:
            data_czas = kurs.get('data_czas', '')
            zysk_str = kurs.get('Zysk netto', '0').replace('zł', '').strip()
            zysk = float(zysk_str)
            
            data_obj = dt.datetime.strptime(data_czas, "%Y-%m-%d %H:%M:%S")
            dzien_tygodnia = data_obj.weekday()
            godzina = data_obj.hour
            
            zarobki_dzien_tygodnia[dzien_tygodnia].append(zysk)
            zarobki_godzina[godzina].append(zysk)
        except:
            continue
    
    # Tworzenie promptów dla różnych typów analizy
    if typ == 'wzorce':
        # Znajdź najlepsze dni i godziny
        najlepszy_dzien = max(zarobki_dzien_tygodnia.items(), 
                             key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0) if zarobki_dzien_tygodnia else (0, [0])
        najlepsza_godzina = max(zarobki_godzina.items(), 
                               key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0) if zarobki_godzina else (0, [0])
        
        dni_pl = ['poniedziałek', 'wtorek', 'środa', 'czwartek', 'piątek', 'sobota', 'niedziela']
        
        prompt = f"""Jesteś ekspertem w analizie danych dla kierowców taxi. Przeanalizuj dane użytkownika i podaj konkretne wzorce czasowe.

DANE UŻYTKOWNIKA:
- Liczba kursów: {ile_kursow}
- Średnia stawka godzinowa: {srednia_stawka:.2f} zł/h
- Całkowity zysk: {suma_zysk:.2f} zł
- Najlepszy dzień tygodnia: {dni_pl[najlepszy_dzien[0]]} (średni zysk: {sum(najlepszy_dzien[1])/len(najlepszy_dzien[1]):.2f} zł)
- Najlepsza godzina: {najlepsza_godzina[0]}:00 (średni zysk: {sum(najlepsza_godzina[1])/len(najlepsza_godzina[1]):.2f} zł)

Napisz krótką, konkretną analizę wzorców czasowych (max 200 słów). Podaj:
1. W które dni tygodnia zarabia najlepiej
2. W jakich godzinach najlepiej jeździć
3. Konkretne rekomendacje kiedy jeździć

Pisz po polsku, bezpośrednio do kierowcy. Używaj konkretnych liczb z danych."""

    elif typ == 'optymalizacja':
        prompt = f"""Jesteś ekspertem w optymalizacji zarobków kierowców taxi. Przeanalizuj dane i podaj konkretne porady.

DANE UŻYTKOWNIKA:
- Liczba kursów: {ile_kursow}
- Średnia stawka godzinowa: {srednia_stawka:.2f} zł/h
- Platformy: {', '.join([f"{p} ({dane['liczba']} kursów)" for p, dane in platformy.items()])}

Napisz konkretne porady jak zwiększyć stawkę godzinową (max 200 słów). Podaj:
1. Co robisz dobrze (na podstawie danych)
2. Co możesz poprawić
3. 3 konkretne działania do wdrożenia od jutra

Pisz po polsku, bezpośrednio do kierowcy. Używaj konkretnych liczb z danych."""

    elif typ == 'platformy':
        platformy_info = []
        for p, dane in platformy.items():
            srednia_p = sum(dane['stawki'])/len(dane['stawki']) if dane['stawki'] else 0
            platformy_info.append(f"{p}: {dane['liczba']} kursów, średnia stawka {srednia_p:.2f} zł/h")
        
        prompt = f"""Jesteś ekspertem w porównywaniu platform taxi. Przeanalizuj dane użytkownika.

DANE PLATFORM:
{chr(10).join(['- ' + info for info in platformy_info])}

Napisz porównanie platform (max 200 słów). Podaj:
1. Która platforma jest najbardziej opłacalna dla tego kierowcy
2. Które platformy warto ograniczyć
3. Konkretne rekomendacje dotyczące wyboru platform

Pisz po polsku, bezpośrednio do kierowcy. Używaj konkretnych liczb z danych."""

    elif typ == 'pytanie':
        # Przygotuj kontekst dla dowolnego pytania
        prompt = f"""Jesteś ekspertem w analizie danych dla kierowców taxi. Odpowiedz na pytanie użytkownika.

DANE UŻYTKOWNIKA:
- Liczba kursów: {ile_kursow}
- Średnia stawka godzinowa: {srednia_stawka:.2f} zł/h
- Całkowity zysk: {suma_zysk:.2f} zł
- Platformy: {', '.join([f"{p} ({dane['liczba']} kursów, średnia {sum(dane['stawki'])/len(dane['stawki']):.2f} zł/h)" for p, dane in platformy.items() if dane['stawki']])}

PYTANIE UŻYTKOWNIKA: {pytanie}

Odpowiedz konkretnie i praktycznie (max 200 słów). Używaj danych użytkownika w odpowiedzi. Pisz po polsku."""
    
    else:
        return jsonify({'analiza': 'Nieznany typ analizy'})
    
    # Wywołaj OpenRouter API
    try:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            return jsonify({
                'analiza': '⚠️ AI Asystent wymaga klucza API OpenRouter.\n\nAby skonfigurować:\n1. Przejdź do zakładki Secrets (🔒)\n2. Dodaj nowy secret:\n   - Key: OPENROUTER_API_KEY\n   - Value: Twój klucz z openrouter.ai\n\n💡 Możesz uzyskać darmowy klucz na https://openrouter.ai'
            })
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': request.host_url,
            },
            json={
                'model': 'qwen/qwen2.5-vl-72b-instruct:free',
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 500,
                'temperature': 0.7
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            analiza_text = result['choices'][0]['message']['content']
            return jsonify({'analiza': analiza_text})
        else:
            return jsonify({
                'analiza': f'Błąd API: {response.status_code}. Sprawdź klucz API i spróbuj ponownie.'
            })
            
    except Exception as e:
        return jsonify({
            'analiza': f'Wystąpił błąd: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
