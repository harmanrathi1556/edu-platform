from supabase import create_client, Client
from config import Config
import json

class Database:
    def __init__(self):
        self.supabase: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    def get_user_by_email(self, email):
        response = self.supabase.table('users').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    
    def get_user_by_id(self, user_id):
        response = self.supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    
    def create_user(self, user_data):
        return self.supabase.table('users').insert(user_data).execute()
    
    def update_user(self, user_id, data):
        return self.supabase.table('users').update(data).eq('id', user_id).execute()
    
    def get_institute_users(self, institute_id):
        return self.supabase.table('users').select('*').eq('institute_id', institute_id).execute()
    
    def get_institutes(self):
        return self.supabase.table('institutes').select('*').execute()
    
    def get_payments(self, institute_id=None):
        if institute_id:
            return self.supabase.table('payments').select('*').eq('institute_id', institute_id).execute()
        return self.supabase.table('payments').select('*').execute()
    
    def get_stats(self):
        users = self.supabase.table('users').select('count').execute()
        institutes = self.supabase.table('institutes').select('count').execute()
        payments = self.supabase.table('payments').select('count').execute()
        return {
            'total_users': users.count,
            'total_institutes': institutes.count,
            'total_payments': payments.count
        }
