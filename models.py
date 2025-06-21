from database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)
    message_type = db.Column(db.String(20), default='user')  # 'user' or 'bot'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'message_type': self.message_type,
            'timestamp': self.timestamp.isoformat(),
            'session_id': self.session_id
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_type = db.Column(db.String(10))
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'filename': self.filename,
            'upload_date': self.upload_date.isoformat(),
            'file_type': self.file_type
        }