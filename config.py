import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL', 
        'postgresql://ai_user:123@localhost:5432/ai_chat_db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # OpenAI Configuration
    CLOUDFLARE_API_KEY = os.getenv('CLOUDFLARE_API_KEY')
    
    # App Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'intern_tasks_secret_key')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # RAG Configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    # Cloudflare Configuration
    CLOUDFLARE_ACCOUNT_ID = os.getenv('CLOUDFLARE_ACCOUNT_ID', 'YOUR_ACCOUNT_ID')
    CLOUDFLARE_MODEL = os.getenv('CLOUDFLARE_MODEL', '@cf/meta/llama-2-7b-chat-fp16')