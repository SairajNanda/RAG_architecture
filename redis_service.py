import redis
import json
from typing import List, Dict, Optional
from config import Config

class RedisService:
    def __init__(self):
        self.redis_client = redis.from_url(Config.REDIS_URL, decode_responses=True)
        self.cache_expiry = 3600  # 1 hour
    
    def cache_message(self, user_id: str, message_data: Dict):
        """Cache recent messages for faster access"""
        key = f"recent_messages:{user_id}"
        try:
            # Add message to list
            self.redis_client.lpush(key, json.dumps(message_data))
            # Keep only last 50 messages
            self.redis_client.ltrim(key, 0, 49)
            # Set expiry
            self.redis_client.expire(key, self.cache_expiry)
            return True
        except Exception as e:
            print(f"Redis cache error: {e}")
            return False
    
    def get_recent_messages(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent messages from cache"""
        key = f"recent_messages:{user_id}"
        try:
            messages = self.redis_client.lrange(key, 0, limit - 1)
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            print(f"Redis get error: {e}")
            return []
    
    def cache_rag_response(self, query: str, response: str):
        """Cache RAG responses for similar queries"""
        key = f"rag_cache:{hash(query)}"
        try:
            self.redis_client.setex(key, self.cache_expiry, response)
            return True
        except Exception as e:
            print(f"Redis RAG cache error: {e}")
            return False
    
    def get_cached_rag_response(self, query: str) -> Optional[str]:
        """Get cached RAG response"""
        key = f"rag_cache:{hash(query)}"
        try:
            return self.redis_client.get(key)
        except Exception as e:
            print(f"Redis RAG get error: {e}")
            return None
    
    def publish_message(self, channel: str, message: Dict):
        """Publish message for real-time updates"""
        try:
            self.redis_client.publish(channel, json.dumps(message))
            return True
        except Exception as e:
            print(f"Redis publish error: {e}")
            return False
    
    def subscribe_to_channel(self, channel: str):
        """Subscribe to channel for real-time updates"""
        try:
            pubsub = self.redis_client.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        except Exception as e:
            print(f"Redis subscribe error: {e}")
            return None