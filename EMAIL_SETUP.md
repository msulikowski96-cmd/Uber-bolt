
# Konfiguracja wysyłania emaili weryfikacyjnych

Aby włączyć wysyłanie emaili weryfikacyjnych, musisz skonfigurować następujące zmienne środowiskowe w zakładce **Secrets**:

## Wymagane zmienne:

1. **SMTP_SERVER** - Serwer SMTP (np. `smtp.gmail.com` dla Gmail)
2. **SMTP_PORT** - Port SMTP (np. `587`)
3. **SMTP_USER** - Adres email, z którego będą wysyłane wiadomości
4. **SMTP_PASSWORD** - Hasło do konta email

## Konfiguracja dla Gmail:

1. Przejdź do: https://myaccount.google.com/security
2. Włącz weryfikację dwuetapową
3. Wygeneruj "Hasło aplikacji" dla Taxi Calculator
4. Użyj tego hasła jako `SMTP_PASSWORD`

## Konfiguracja w Replit:

1. Kliknij ikonę 🔒 **Secrets** w lewym panelu
2. Dodaj zmienne:
   - Key: `SMTP_SERVER`, Value: `smtp.gmail.com`
   - Key: `SMTP_PORT`, Value: `587`
   - Key: `SMTP_USER`, Value: `twoj.email@gmail.com`
   - Key: `SMTP_PASSWORD`, Value: `hasło aplikacji z Gmail`

## Alternatywne serwery SMTP:

- **SendGrid**: smtp.sendgrid.net:587
- **Mailgun**: smtp.mailgun.org:587
- **Outlook/Hotmail**: smtp-mail.outlook.com:587

## Testowanie:

Po skonfigurowaniu, spróbuj zarejestrować nowe konto. Powinieneś otrzymać email z linkiem aktywacyjnym.
