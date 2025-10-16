
# Deployment Guide

## ✅ Aktualna Konfiguracja Secrets

Wszystkie wymagane zmienne środowiskowe są już skonfigurowane:

### Obowiązkowe (✅ Skonfigurowane):
1. ✅ **SESSION_SECRET** - Klucz sesji Flask
2. ✅ **DATABASE_URL** - PostgreSQL connection string (Neon DB)
3. ✅ **OPENROUTER_API_KEY** - Klucz API dla AI Asystenta

### Opcjonalne (⚠️ Do rozważenia):
- **UBER_CLIENT_ID** - Dla przyszłej integracji z Uber API
- **UBER_CLIENT_SECRET** - Dla przyszłej integracji z Uber API

## Deployment Steps:

### Opcja 1: Automatyczne wdrożenie (Zalecane)
1. Kliknij przycisk **Deploy** w prawym górnym rogu
2. Wybierz typ deploymentu:
   - **Autoscale** (zalecane dla produkcji - automatyczne skalowanie)
   - **Reserved VM** (stała moc obliczeniowa)
3. Deployment zostanie automatycznie skonfigurowany z `gunicorn`

### Opcja 2: Ręczna konfiguracja
Jeśli potrzebujesz dostosować ustawienia:

```bash
# Build command (opcjonalnie, jeśli kompilacja wymagana)
# Nie wymagane dla tej aplikacji

# Run command (automatycznie ustawione)
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Weryfikacja po deploymencie:

Po wdrożeniu sprawdź:
- [ ] Strona logowania działa (HTTPS)
- [ ] Rejestracja nowych użytkowników
- [ ] Zapisywanie kursów do PostgreSQL
- [ ] Wyświetlanie statystyk
- [ ] PWA installation banner (na mobile)
- [ ] AI Asystent (jeśli OPENROUTER_API_KEY skonfigurowany)

## Troubleshooting:

### Problem: Błąd sesji
**Rozwiązanie:** SESSION_SECRET jest już ustawiony (64 znaki)

### Problem: Błąd bazy danych
**Rozwiązanie:** DATABASE_URL jest poprawnie skonfigurowany dla Neon PostgreSQL

### Problem: AI Asystent nie działa
**Rozwiązanie:** OPENROUTER_API_KEY jest już skonfigurowany

### Problem: HTTPS nie działa
**Rozwiązanie:** Replit automatycznie obsługuje HTTPS w deploymencie

## Monitorowanie:

Po deploymencie możesz monitorować:
- **Logs** - W zakładce Deployments > Logs
- **Performance** - Metrics w panelu Deployment
- **Database** - Neon Dashboard dla PostgreSQL

## Backup danych użytkowników:

Dane kursów są przechowywane w:
- PostgreSQL (dane użytkowników)
- `user_data/{user_id}/` (pliki kursów i celów)

Zalecane jest regularne tworzenie backupów z Neon Dashboard.
