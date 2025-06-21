from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import os
import PyPDF2
import requests
from config import Config
import faiss

class RAGService:
    def __init__(self):
        self.cloudflare_api_key = Config.CLOUDFLARE_API_KEY
        self.cloudflare_account_id = getattr(Config, 'CLOUDFLARE_ACCOUNT_ID', '91d07396969bbe837933a876cb257b0c')  # Set this in config.py or .env
        self.cloudflare_model = getattr(Config, 'CLOUDFLARE_MODEL', '@cf/meta/llama-2-7b-chat-fp16')
        # Use sentence transformers for embeddings
        self.embeddings_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP,
            length_function=len,
        )
        
        self.index = None  # FAISS index
        self.chunk_id_to_text = []  # Maps index to chunk text
        self.documents = []
    
    def load_document(self, file_path: str) -> str:
        """Load document content from file"""
        try:
            if file_path.endswith('.pdf'):
                return self._extract_pdf_text(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                raise ValueError("Unsupported file format")
        except Exception as e:
            print(f"Error loading document: {e}")
            return ""
    
    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text from PDF file"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text()
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
        return text
    
    def process_document(self, content: str):
        """Process document and add to FAISS index"""
        try:
            # Split text into chunks
            chunks = self.text_splitter.split_text(content)
            if not hasattr(self, 'documents') or self.documents is None:
                self.documents = []
            self.documents.extend(chunks)

            # Use sentence transformers for embeddings
            embeddings = self.embeddings_model.encode(chunks)
            embeddings = np.array(embeddings).astype('float32')

            if self.index is None:
                self.index = faiss.IndexFlatL2(embeddings.shape[1])
                self.index.add(embeddings)
                self.chunk_id_to_text = list(chunks)
            else:
                self.index.add(embeddings)
                self.chunk_id_to_text.extend(chunks)

            print(f"Processed {len(chunks)} new document chunks, total: {len(self.documents)}")
            return True
        except Exception as e:
            print(f"Error processing document: {e}")
            return False
    
    def query_documents(self, query: str, k: int = 3) -> List[str]:
        """Query documents and return relevant chunks"""
        if self.index is None or len(self.chunk_id_to_text) == 0:
            return []

        try:
            query_embedding = self.embeddings_model.encode([query]).astype('float32')
            D, I = self.index.search(query_embedding, k)
            indices = I[0]
            return [self.chunk_id_to_text[i] for i in indices if i < len(self.chunk_id_to_text)]
        except Exception as e:
            print(f"Error querying documents: {e}")
            return []
    
    def generate_answer(self, query: str, context: list) -> str:
        """Generate answer using Cloudflare Workers AI with context"""
        try:
            context_text = "\n\n".join(context)
            prompt = f"""Based on the following context, answer the question. If the answer cannot be found in the context, say so.\n\nContext:\n{context_text}\n\nQuestion: {query}\n\nAnswer:"""
            url = f"https://api.cloudflare.com/client/v4/accounts/{self.cloudflare_account_id}/ai/run/{self.cloudflare_model}"
            headers = {
                "Authorization": f"Bearer {self.cloudflare_api_key}",
                "Content-Type": "application/json"
            }
            data = {"prompt": prompt}
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 200:
                result = response.json()
                # Cloudflare returns result["result"]["response"]
                return result.get("result", {}).get("response", "No answer generated.")
            else:
                return f"Error from Cloudflare Workers AI: {response.status_code} {response.text}"
        except Exception as e:
            print(f"Error generating answer: {e}")
            return f"Error generating response: {str(e)}"
    
    def ask_question(self, question: str, threshold: float = 0.5) -> Dict:
        """Main method to ask questions and get answers"""
        try:
            relevant_docs = self.query_documents(question)
            confidence = len(relevant_docs) / 3  

            if not relevant_docs or confidence < threshold:
                # Fallback: Call Workers AI LLM directly
                answer = self.generate_answer(question, [])  
                return {
                    "answer": answer,
                    "sources": [],
                    "confidence": confidence,
                    "source": "llm" 
                }
            else:
                # Use RAG as usual
                answer = self.generate_answer(question, relevant_docs)
                return {
                    "answer": answer,
                    "sources": relevant_docs[:2],
                    "confidence": confidence,
                    "source": "context"
                }
        except Exception as e:
            return {
                "answer": f"Error processing question: {str(e)}",
                "sources": [],
                "confidence": 0,
                "source": "error"
            }
    
    def load_and_process_context_directory(self, directory_path: str):
        """Load and process all .txt and .pdf documents from a directory for RAG."""
        processed_files = []
        for filename in os.listdir(directory_path):
            if filename.endswith('.txt') or filename.endswith('.pdf'):
                file_path = os.path.join(directory_path, filename)
                content = self.load_document(file_path)
                if content:
                    success = self.process_document(content)
                    if success:
                        processed_files.append(filename)
        print(f"Processed files from context directory: {processed_files}")