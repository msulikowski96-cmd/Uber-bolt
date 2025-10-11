import datetime

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
        return

    dzisiaj = datetime.datetime.now().strftime("%Y-%m-%d")
    stawki = []
    nowe_linie = []
    podsumowanie_dnia = f"📊 Podsumowanie dnia {dzisiaj}"

    for linia in linie:
        if linia.startswith("📊 Podsumowanie dnia") and dzisiaj in linia:
            continue  # usuwamy stare podsumowanie dzisiejszego dnia
        nowe_linie.append(linia)
        if linia.startswith("["):
            data = linia[1:11]  # YYYY-MM-DD
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

def oblicz_oplacalnosc():
    print("=== Kalkulator opłacalności kursu ===\n")

    dystans_dojazdu = float(input("Dystans dojazdu do klienta (km): "))
    czas_dojazdu = float(input("Czas dojazdu do klienta (min): "))
    dystans_kursu = float(input("Dystans z klientem (km): "))
    czas_kursu = float(input("Czas trwania kursu (min): "))
    kwota = float(input("Kwota za kurs (z napiwkiem) [zł]: "))
    procent_dla_kierowcy = float(input("Procent dla kierowcy (np. 60): "))
    spalanie = float(input("Średnie spalanie auta (l/100km): "))
    cena_paliwa = float(input("Cena paliwa (zł/litr): "))

    dystans_calkowity = dystans_dojazdu + dystans_kursu
    czas_calkowity_h = (czas_dojazdu + czas_kursu) / 60
    koszt_paliwa = (dystans_calkowity * spalanie / 100) * cena_paliwa
    zarobek_dla_kierowcy = kwota * (procent_dla_kierowcy / 100)
    zysk_netto = zarobek_dla_kierowcy - koszt_paliwa
    stawka_godzinowa = zysk_netto / czas_calkowity_h if czas_calkowity_h > 0 else 0

    if stawka_godzinowa >= 50:
        ocena = "💰 Kurs bardzo opłacalny!"
    elif stawka_godzinowa >= 30:
        ocena = "👍 Kurs opłacalny."
    elif stawka_godzinowa >= 20:
        ocena = "😐 Kurs średnio opłacalny."
    else:
        ocena = "❌ Kurs nieopłacalny."

    print("\n=== Wyniki analizy ===")
    print(f"Dystans całkowity: {dystans_calkowity:.2f} km")
    print(f"Czas całkowity: {czas_calkowity_h:.2f} godz.")
    print(f"Koszt paliwa: {koszt_paliwa:.2f} zł")
    print(f"Zarobek kierowcy (po prowizji): {zarobek_dla_kierowcy:.2f} zł")
    print(f"Zysk netto po paliwie: {zysk_netto:.2f} zł")
    print(f"Średnia stawka godzinowa: {stawka_godzinowa:.2f} zł/h")
    print(f"Ocena: {ocena}")
    print("=====================================")

    dane = {
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

    zapisz_do_pliku(dane)
    aktualizuj_srednia_dnia()
    print("\n✅ Wyniki zapisano w pliku 'kursy.txt'. Średnia stawka dnia została zaktualizowana.")

if __name__ == "__main__":
    oblicz_oplacalnosc()