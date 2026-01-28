# AI-Powered RAG Chatbot for Financial & Insurance Records


Technologies: Python, FastAPI, PyTorch, Hugging Face Transformers, FAISS, CLIP, React.js, Tailwind CSS.

Developed a hybrid RAG architecture combining structured data retrieval (SQL/Pandas) with semantic search to provide accurate answers regarding insurance claims and policies.

Implemented a local LLM inference pipeline using Qwen1.5-0.5B and Hugging Face Transformers to generate natural language responses based on retrieved context, ensuring data privacy by running entirely offline.

Engineered a multi-modal retrieval system that utilizes Regex pattern matching for precise ID lookups (Policy/Claim IDs) and CLIP embeddings with FAISS index for semantic FAQ matching.

Built a high-performance REST API with FastAPI to serve model predictions and handle frontend requests, ensuring low-latency communication between the React UI and the Python backend.
