"""
Moduł do komunikacji z Uber Driver API
Obsługuje OAuth 2.0 i pobieranie danych o kursach kierowcy
"""

import os
import requests
from datetime import datetime, timedelta
import json


class UberDriverAPI:
    """Klasa do obsługi komunikacji z Uber Driver API"""
    
    def __init__(self, sandbox=True):
        self.client_id = os.environ.get('UBER_CLIENT_ID')
        self.client_secret = os.environ.get('UBER_CLIENT_SECRET')
        self.server_token = os.environ.get('UBER_SERVER_TOKEN')
        self.sandbox = sandbox
        
        if sandbox:
            self.base_url = 'https://sandbox-api.uber.com/v1.2'
            self.auth_url = 'https://sandbox-login.uber.com/oauth/v2/token'
        else:
            self.base_url = 'https://api.uber.com/v1.2'
            self.auth_url = 'https://login.uber.com/oauth/v2/token'
        
        self.access_token = None
        
    def authenticate(self, code=None):
        """
        Uwierzytelnienie OAuth 2.0 używając Client Credentials flow
        
        Args:
            code: Kod autoryzacyjny (nieużywany w client credentials)
        
        Returns:
            bool: True jeśli sukces, False jeśli błąd
        """
        if self.server_token:
            self.access_token = self.server_token
            return True
        
        if not self.client_id or not self.client_secret:
            print("Brak UBER_CLIENT_ID lub UBER_CLIENT_SECRET")
            return False
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': 'client_credentials',
            'scope': 'partner.trips partner.payments profile'
        }
        
        try:
            response = requests.post(self.auth_url, data=data)
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            print(f"Token otrzymany: {self.access_token[:20]}..." if self.access_token else "Brak tokenu")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"Błąd uwierzytelnienia HTTP: {e}")
            print(f"Odpowiedź: {e.response.text}")
            return False
        except Exception as e:
            print(f"Błąd uwierzytelnienia: {e}")
            return False
    
    def get_trips(self, start_date=None, end_date=None, limit=50):
        """
        Pobiera historię kursów kierowcy
        
        Args:
            start_date: Data początkowa (datetime)
            end_date: Data końcowa (datetime)
            limit: Maksymalna liczba kursów do pobrania
        
        Returns:
            list: Lista kursów lub None w przypadku błędu
        """
        if not self.access_token:
            print("Brak tokenu dostępu - najpierw wywołaj authenticate()")
            return None
        
        # Domyślnie pobierz kursy z ostatnich 30 dni
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        url = f'{self.base_url}/partners/trips'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept-Language': 'pl-PL',
            'Content-Type': 'application/json'
        }
        
        params = {
            'from_time': int(start_date.timestamp()),
            'to_time': int(end_date.timestamp()),
            'limit': limit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get('trips', [])
        except requests.exceptions.HTTPError as e:
            print(f"Błąd HTTP: {e}")
            print(f"Odpowiedź: {e.response.text}")
            return None
        except Exception as e:
            print(f"Błąd pobierania kursów: {e}")
            return None
    
    def get_trip_details(self, trip_id):
        """
        Pobiera szczegóły pojedynczego kursu
        
        Args:
            trip_id: ID kursu
        
        Returns:
            dict: Szczegóły kursu lub None w przypadku błędu
        """
        if not self.access_token:
            print("Brak tokenu dostępu")
            return None
        
        url = f'{self.base_url}/partners/trips/{trip_id}'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept-Language': 'pl-PL',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Błąd pobierania szczegółów kursu: {e}")
            return None
    
    def get_driver_profile(self):
        """
        Pobiera profil kierowcy
        
        Returns:
            dict: Dane profilu lub None w przypadku błędu
        """
        if not self.access_token:
            print("Brak tokenu dostępu")
            return None
        
        url = f'{self.base_url}/partners/me'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept-Language': 'pl-PL',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Błąd pobierania profilu: {e}")
            return None
    
    def get_earnings(self, start_date=None, end_date=None):
        """
        Pobiera zarobki kierowcy
        
        Args:
            start_date: Data początkowa (datetime)
            end_date: Data końcowa (datetime)
        
        Returns:
            dict: Dane zarobków lub None w przypadku błędu
        """
        if not self.access_token:
            print("Brak tokenu dostępu")
            return None
        
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        url = f'{self.base_url}/partners/payments'
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept-Language': 'pl-PL',
            'Content-Type': 'application/json'
        }
        
        params = {
            'from_time': int(start_date.timestamp()),
            'to_time': int(end_date.timestamp())
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Błąd pobierania zarobków: {e}")
            return None
    
    def convert_trip_to_app_format(self, trip):
        """
        Konwertuje dane kursu z Uber API do formatu aplikacji
        
        Args:
            trip: Dane kursu z API Uber
        
        Returns:
            dict: Dane w formacie aplikacji
        """
        try:
            # Konwersja timestampu na datetime
            start_time = datetime.fromtimestamp(trip.get('start_time', 0))
            end_time = datetime.fromtimestamp(trip.get('end_time', 0))
            
            # Obliczanie czasu trwania w minutach
            duration_minutes = (end_time - start_time).total_seconds() / 60
            
            # Dystans w kilometrach (Uber zwraca w milach)
            distance_miles = trip.get('distance', 0)
            distance_km = distance_miles * 1.60934
            
            # Kwota (Uber zwraca w centach/groszach)
            fare_amount = trip.get('fare', {}).get('amount', 0) / 100
            
            # Format dla aplikacji
            return {
                'timestamp': start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'dystans_dojazd': 0,  # Uber nie dostarcza tej informacji
                'czas_dojazd': 0,
                'dystans_kurs': distance_km,
                'czas_kurs': duration_minutes,
                'kwota': fare_amount,
                'koszt_paliwa': 0,  # Należy obliczyć osobno
                'platforma': 'Uber',
                'trip_id': trip.get('trip_id', '')
            }
        except Exception as e:
            print(f"Błąd konwersji danych kursu: {e}")
            return None


def test_connection():
    """Funkcja testowa do sprawdzenia połączenia z API"""
    api = UberDriverAPI()
    
    if not api.client_id or not api.server_token:
        return {
            'success': False,
            'message': 'Brak kluczy API. Ustaw UBER_CLIENT_ID i UBER_SERVER_TOKEN.'
        }
    
    if api.authenticate():
        profile = api.get_driver_profile()
        if profile:
            return {
                'success': True,
                'message': 'Połączenie z Uber API działa!',
                'driver_name': profile.get('first_name', 'Nieznany')
            }
    
    return {
        'success': False,
        'message': 'Nie udało się połączyć z Uber API'
    }
