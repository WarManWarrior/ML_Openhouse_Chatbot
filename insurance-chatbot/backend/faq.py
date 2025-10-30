import pandas as pd
import torch
from transformers import CLIPProcessor, CLIPModel
from faiss import IndexFlatL2
import numpy as np
import os

class ClipFaqRAG:
    """
    RAG Agent using CLIP embeddings and FAISS for similarity search on FAQs.
    This is designed to handle general questions when no specific ID is provided.
    """
    def __init__(self, data_directory, faq_filename='faqs.csv'):
        self.faq_path = os.path.join(data_directory, faq_filename)
        self.df = None
        self.processor = None
        self.model = None
        self.index = None
        self._load_and_index()

    def _load_and_index(self):
        print("\nInitializing CLIP-FAISS RAG Agent...")
        try:
            # 1. Load Data
            self.df = pd.read_csv(self.faq_path).fillna('')
            if self.df.empty:
                print(f"Warning: '{self.faq_path}' is empty or not found.")
                return

            # 2. Initialize CLIP
            # Use a text-to-text model's components for simplicity, though CLIP is generally multimodal.
            # We'll use the text part of CLIP for embedding the questions.
            self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.model.eval()

            # 3. Create Embeddings
            print("Creating CLIP embeddings for FAQs...")
            faq_questions = self.df['Question'].tolist()
            embeddings = []
            with torch.no_grad():
                # CLIP text encoder
                inputs = self.processor(text=faq_questions, return_tensors="pt", padding=True, truncation=True)
                text_features = self.model.get_text_features(**inputs).cpu().numpy()
                embeddings = text_features

            # 4. Build FAISS Index
            dimension = embeddings.shape[1]
            self.index = IndexFlatL2(dimension)
            self.index.add(embeddings)
            print(f"FAISS index built with {self.index.ntotal} vectors.")

        except FileNotFoundError:
            print(f"Error: FAQ file not found at '{self.faq_path}'.")
        except Exception as e:
            print(f"Error during CLIP-FAISS initialization: {e}")

    def get_embedding(self, text):
        """Helper to get the embedding for a new query."""
        with torch.no_grad():
            inputs = self.processor(text=[text], return_tensors="pt", padding=True, truncation=True)
            text_features = self.model.get_text_features(**inputs).cpu().numpy()
        return text_features

    def query_faqs(self, query, k=1):
        """Finds the top k nearest FAQ answers."""
        if self.index is None:
            return "CLIP-FAISS RAG Agent is not initialized. Cannot search FAQs."

        query_embedding = self.get_embedding(query)
        # D: distances, I: indices
        D, I = self.index.search(query_embedding.astype(np.float32), k)

        # Retrieve the relevant FAQ row based on the nearest index (I[0][0])
        # We can add a simple distance threshold check here if desired (e.g., D[0][0] < threshold)
        if I[0][0] != -1: # FAISS returns -1 if nothing is found (shouldn't happen with L2)
            match_index = I[0][0]
            context = {
                'Question': self.df.loc[match_index, 'Question'],
                'Answer': self.df.loc[match_index, 'Answer']
            }
            return context
        return "No close match found in the FAQ database."