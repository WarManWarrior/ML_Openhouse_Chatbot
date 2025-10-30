import os
from main import InsuranceRAGChatbot # Assuming main.py is available
from faq import ClipFaqRAG

# --- Main Execution Block ---
DATA_DIR = 'data'
FAQ_FILE = 'faqs.csv' # Assuming the FAQ CSV is named this inside 'data'

if os.path.exists(DATA_DIR):
    # 1. Initialize the main RAG chatbot (which loads all data and LLM)
    chatbot = InsuranceRAGChatbot(DATA_DIR)
    
    # 2. Initialize the new CLIP-FAISS RAG agent for general questions
    # Note: It is assumed 'faqs.csv' is one of the files loaded by the main chatbot
    # but the CLIP-FAISS agent specifically uses the 'faqs.csv' name here for indexing.
    clip_rag = ClipFaqRAG(DATA_DIR, faq_filename=FAQ_FILE)

    print("\n--- Live RAG Insurance Chatbot is Ready! ---")
    print("Ask a question containing a Claim ID, Policy Number, or Customer ID, OR a general question.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            print("Chatbot: Goodbye!")
            break

        # Check for ID first using the main chatbot's internal logic
        found_id, id_type = chatbot._find_id_and_data(user_input)

        if found_id:
            # If an ID is found, use the existing RAG logic in main.py
            response = chatbot.generate_response(user_input)
        else:
            # If no ID is found, execute the new CLIP-FAISS RAG agent
            print("🔎 No ID found. Searching general FAQs with CLIP-FAISS...")
            faq_context = clip_rag.query_faqs(user_input)

            if isinstance(faq_context, str): # Error or No match
                response = faq_context
            else:
                # Use the main chatbot's LLM pipeline for a generative answer based on the retrieved FAQ
                print("Retrieving context from CLIP-FAISS and generating response...")
                
                # --- LLM Response Generation using retrieved context ---
                if not chatbot.llm_pipeline:
                    response = "The Language Model is not available. Please check the initialization errors."
                else:
                    messages = [
                        {"role": "system", "content": ("You are an expert insurance support agent. Your task is to answer the user's query with "
                    "professionalism and accuracy, using *only* the information provided in the context below. "
                    "Do not infer or assume any information. If the answer is not in the context, "
                    "state that you cannot find the information in their records.")},
                    ]
                    
                    info_lines = [f"Retrieved FAQ Question: {faq_context['Question']}", 
                                  f"Retrieved FAQ Answer: {faq_context['Answer']}"]
                                  
                    messages.append({"role": "user", "content": f"Context:\n" + '\n'.join(info_lines) + f"\nQuery: {user_input}\nAnswer:"})
                    
                    prompt = chatbot.llm_pipeline.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                    outputs = chatbot.llm_pipeline(prompt, max_new_tokens=128, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
                    # The main chatbot's method of extracting the answer from the output
                    llm_answer = outputs[0]["generated_text"].split("Answer:")[1].strip()
                    response = llm_answer
                    
        print(f"Chatbot: {response}\n")
else:
    print(f"Error: Please create a directory named '{DATA_DIR}' and place your CSV files inside it.")