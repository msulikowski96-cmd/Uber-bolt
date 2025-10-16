
# Deployment Guide

## Wymagane Secrets (Environment Variables)

Przed wdrożeniem aplikacji, skonfiguruj następujące zmienne środowiskowe w zakładce Secrets (🔒):

### Obowiązkowe:
1. **SESSION_SECRET** - Klucz sesji Flask (minimum 32 znaki losowe)
   - Przykład: `openssl rand -hex 32` w terminalu

2. **DATABASE_URL** - URL połączenia z PostgreSQL
   - Format: `postgresql://user:password@host:port/database`
   - Jeśli używasz Neon/Replit DB, skopiuj connection string

### Opcjonalne:
3. **OPENROUTER_API_KEY** - Klucz API dla AI Asystenta
   - Zdobądź na: https://openrouter.ai
   - Model: `qwen/qwen2.5-vl-72b-instruct:free` (darmowy)

## Deployment Steps:

1. Kliknij przycisk **Deploy** w prawym górnym rogu
2. Wybierz typ deploymentu (zalecane: Autoscale lub Reserved VM)
3. Skonfiguruj secrets wymienione powyżej
4. Kliknij **Deploy**

## Weryfikacja:

Po deploymencie sprawdź:
- [ ] Strona logowania działa
- [ ] Rejestracja nowych użytkowników
- [ ] Zapisywanie kursów
- [ ] Wyświetlanie statystyk
- [ ] PWA installation banner (na mobile)

## Troubleshooting:

**Problem: Błąd sesji**
- Sprawdź czy SESSION_SECRET jest ustawiony

**Problem: Błąd bazy danych**
- Sprawdź poprawność DATABASE_URL
- Upewnij się że baza PostgreSQL jest dostępna

**Problem: AI Asystent nie działa**
- To normalne jeśli nie masz OPENROUTER_API_KEY
- Dodaj klucz w Secrets aby włączyć funkcję
