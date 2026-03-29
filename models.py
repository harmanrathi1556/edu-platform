import requests
import json
from config import Config

class Database:
    def __init__(self):
        self.url = Config.SUPABASE_URL
        self.key = Config.SUPABASE_KEY
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
        }
    
    def _request(self, method, endpoint, data=None):
        url = f"{self.url}/rest/v1/{endpoint}"
        response = requests.request(method, url, headers=self.headers, json=data)
        return response.json()
    
    def get_user_by_email(self, email):
        data = self._request('GET', 'users', {'email': {'_eq': email}})
        return data[0] if data else None
    
    def get_user_by_id(self, user_id):
        data = self._request('GET', 'users', {'id': {'_eq': user_id}})
        return data[0] if data else None
    
    def create_user(self, user_data):
        return self._request('POST', 'users', user_data)
    
    def update_user(self, user_id, data):
        return self._request('PATCH', 'users', data, params={'id': {'_eq': user_id}})
    
    def get_institutes(self):
        return self._request('GET', 'institutes')
    
    def get_stats(self):
        users = self._request('GET', 'users?select=count')
        institutes = self._request('GET', 'institutes?select=count')
        payments = self._request('GET', 'payments?select=count')
        return {
            'total_users': len(users) if users else 0,
            'total_institutes': len(institutes) if institutes else 0,
            'total_payments': len(payments) if payments else 0
        }
