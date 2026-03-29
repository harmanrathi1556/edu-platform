import requests
import json
from config import Config

class Database:
    def __init__(self):
        self.url = getattr(Config, 'SUPABASE_URL', '')
        self.key = getattr(Config, 'SUPABASE_KEY', '')
        self.headers = {
            'apikey': self.key,
            'Authorization': f'Bearer {self.key}',
            'Content-Type': 'application/json',
        }
    
    def _request(self, method, endpoint, params=None, data=None):
        if not self.url or not self.key:
            print("❌ Missing Supabase config")
            return []
        
        url = f"{self.url}/rest/v1/{endpoint}"
        try:
            response = requests.request(
                method, 
                url, 
                headers=self.headers, 
                params=params,
                json=data,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                return result if isinstance(result, list) else [result]
            else:
                print(f"Supabase {response.status_code}: {endpoint}")
                return []
        except Exception as e:
            print(f"Request failed: {e}")
            return []
    
    def get_user_by_email(self, email):
        data = self._request('GET', 'users', {'email': {'_eq': email}})
        return data[0] if data else None
    
    def get_user_by_id(self, user_id):
        data = self._request('GET', 'users', {'id': {'_eq': user_id}})
        return data[0] if data else None
    
    def create_user(self, user_data):
        return self._request('POST', 'users', data=user_data)
    
    def update_user(self, user_id, data):
        self._request('PATCH', 'users', params={'id': {'_eq': user_id}}, data=data)
    
    def get_institutes(self):
        return self._request('GET', 'institutes?limit=10')
    
    def get_stats(self):
        try:
            users = self._request('GET', 'users?select=id')
            institutes = self._request('GET', 'institutes?select=id')
            payments = self._request('GET', 'payments?select=id')
            return {
                'total_users': len(users),
                'total_institutes': len(institutes),
                'total_payments': len(payments)
            }
        except:
            return {
                'total_users': 0,
                'total_institutes': 0, 
                'total_payments': 0
            }
