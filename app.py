from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from database import db, init_db
from models import ChatMessage, Document
from rag_service import RAGService
from redis_service import RedisService
from config import Config
import uuid
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
CORS(app)
init_db(app)

# Initialize services
rag_service = RAGService()
redis_service = RedisService()

# Create upload directory
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load all documents from context directory on startup
context_dir = 'context'
if os.path.exists(context_dir):
    rag_service.load_and_process_context_directory(context_dir)
    print("All context documents loaded successfully")

# Frontend Routes
@app.route('/')
def index():
    """Main chat interface"""
    return render_template('index.html')

@app.route('/upload')
def upload_page():
    """Document upload page"""
    return render_template('upload.html')

# API Routes
@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "message": "AI Chat Application API",
        "status": "running",
        "endpoints": {
            "send_message": "POST /api/chat/send",
            "get_messages": "GET /api/chat/messages/<user_id>",
            "ask_question": "POST /api/chat/ask",
            "upload_document": "POST /api/documents/upload"
        }
    })

@app.route('/api/chat/send', methods=['POST'])
def send_message():
    """Send a chat message"""
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'message' not in data or 'user_id' not in data:
            return jsonify({"error": "Missing required fields: message, user_id"}), 400
        
        user_id = data['user_id']
        message = data['message']
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Create and save message
        chat_message = ChatMessage(
            user_id=user_id,
            message=message,
            message_type='user',
            session_id=session_id
        )
        
        db.session.add(chat_message)
        db.session.commit()
        
        # Cache message in Redis
        message_data = chat_message.to_dict()
        redis_service.cache_message(user_id, message_data)
        
        # Publish for real-time updates
        redis_service.publish_message(f"chat:{user_id}", message_data)
        
        return jsonify({
            "success": True,
            "message": "Message sent successfully",
            "data": message_data
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/messages/<user_id>', methods=['GET'])
def get_messages(user_id):
    """Get chat messages for a user"""
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        session_id = request.args.get('session_id')
        
        # Try to get from Redis cache first
        cached_messages = redis_service.get_recent_messages(user_id, per_page)
        
        if cached_messages:
            return jsonify({
                "success": True,
                "data": cached_messages,
                "source": "cache"
            })
        
        # If not in cache, get from database
        query = ChatMessage.query.filter_by(user_id=user_id)
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        messages = query.order_by(ChatMessage.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            "success": True,
            "data": [msg.to_dict() for msg in messages.items],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": messages.total,
                "pages": messages.pages
            },
            "source": "database"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/ask', methods=['POST'])
def ask_question():
    """Ask a question using RAG"""
    try:
        data = request.get_json()
        
        if not data or 'question' not in data or 'user_id' not in data:
            return jsonify({"error": "Missing required fields: question, user_id"}), 400
        
        user_id = data['user_id']
        question = data['question']
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        # Check Redis cache for similar questions
        cached_response = redis_service.get_cached_rag_response(question)
        
        if cached_response:
            # Save cached response to database
            ai_message = ChatMessage(
                user_id=user_id,
                message=question,
                response=cached_response,
                message_type='ai',
                session_id=session_id
            )
            db.session.add(ai_message)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "data": {
                    "question": question,
                    "answer": cached_response,
                    "source": "cache",
                    "message_id": str(ai_message.id)
                }
            })
        
        # Get RAG response
        rag_response = rag_service.ask_question(question)
        answer = rag_response['answer']
        
        # Cache the response
        redis_service.cache_rag_response(question, answer)
        
        # Save to database
        ai_message = ChatMessage(
            user_id=user_id,
            message=question,
            response=answer,
            message_type='ai',
            session_id=session_id
        )
        
        db.session.add(ai_message)
        db.session.commit()
        
        # Cache in Redis
        message_data = ai_message.to_dict()
        redis_service.cache_message(user_id, message_data)
        
        # Publish for real-time updates
        redis_service.publish_message(f"chat:{user_id}", message_data)
        
        return jsonify({
            "success": True,
            "data": {
                "question": question,
                "answer": answer,
                "sources": rag_response.get('sources', []),
                "confidence": rag_response.get('confidence', 0),
                "message_id": str(ai_message.id)
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """Upload and process a document for RAG"""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename.lower().endswith(('.txt', '.pdf')):
            return jsonify({"error": "Only TXT and PDF files are supported"}), 400
        
        # Save file to uploads directory
        filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # Load and process document
            content = rag_service.load_document(file_path)
            
            if not content:
                return jsonify({"error": "Could not extract content from file"}), 400
            
            # Process with RAG
            success = rag_service.process_document(content)
            
            if not success:
                return jsonify({"error": "Failed to process document"}), 500
            
            # Save to database
            document = Document(
                filename=file.filename,
                content=content[:1000],  # Store first 1000 chars for reference
                file_type=file.filename.split('.')[-1].lower()
            )
            
            db.session.add(document)
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": "Document uploaded and processed successfully",
                "document_id": str(document.id),
                "filename": file.filename
            })
            
        except Exception as e:
            # Clean up file on error
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/documents', methods=['GET'])
def get_documents():
    """Get list of uploaded documents"""
    try:
        documents = Document.query.order_by(Document.upload_date.desc()).all()
        
        return jsonify({
            "success": True,
            "data": [doc.to_dict() for doc in documents]
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)