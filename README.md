# AI Chat Application with RAG and Cloudflare Workers AI

This project is a Flask-based AI chat application that uses Retrieval-Augmented Generation (RAG) to answer user questions based on uploaded documents. It integrates with Cloudflare Workers AI for language model responses and supports both text and PDF document ingestion.

## Features
- **Chat with AI**: Ask questions and get answers based on your uploaded documents.
- **Document Upload**: Upload `.txt` or `.pdf` files to provide context for the AI.
- **RAG Pipeline**: Uses FAISS for vector search and sentence-transformers for embeddings.
- **Cloudflare Workers AI**: Uses Cloudflare's LLM API for generating answers.
- **Frontend**: Modern Bootstrap UI with chat and document upload pages.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/SairajNanda/RAG_architecture.git
```

### 2. Install Dependencies
It is recommended to use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the project root with the following content:
```env
CLOUDFLARE_API_KEY=your_cloudflare_api_token_here
CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id_here
CLOUDFLARE_MODEL=@cf/meta/llama-2-7b-chat-fp16
SECRET_KEY=your_flask_secret_key
DATABASE_URL=postgresql://ai_user:123@localhost:5432/ai_chat_db
REDIS_URL=redis://localhost:6379/0
```
- Replace the values with your actual credentials.
- The default model is `@cf/meta/llama-2-7b-chat-fp16`, but you can change it if needed.

### 4. Run the Application
```bash
python app.py
```
The app will be available at [http://localhost:5001](http://localhost:5001).

## Usage
- **Chat**: Go to the main page and start chatting with the AI.
- **Upload Document**: Use the "Upload Document" tab to upload `.txt` or `.pdf` files. The AI will use these as context for answering questions.

## Project Structure
```
intern_task/
├── app.py                # Main Flask app
├── config.py             # Configuration and environment variables
├── rag_service.py        # RAG logic and Cloudflare Workers AI integration
├── redis_service.py      # Redis caching
├── models.py             # SQLAlchemy models
├── database.py           # DB initialization
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── document.txt          # Example document
├── static/               # CSS, JS, and uploads
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   └── upload.html
└── ...
```

## Notes
- Ensure your Cloudflare API token has permission to use Workers AI.
- The app uses FAISS for fast vector search and sentence-transformers for embeddings.
- Uploaded documents are stored in `static/uploads/`.
- The default database is PostgreSQL; you can change the `DATABASE_URL` in `.env`.

## License
MIT License 