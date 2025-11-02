import pandas as pd
import re
import os
import torch
from transformers import pipeline

class InsuranceRAGChatbot:
    """
    Improved version: Retrieves and combines relevant context from policy, claim, and FAQ datasets,
    providing detailed answers even if only a partial match is found.
    """
    def __init__(self, data_directory):
        self.faq_df = None
        self.claims_df = None
        self.policy_df = None
        self.llm_pipeline = None
        self._load_data(data_directory)
        self._initialize_llm()
        self.messages = [
                {"role": "system", "content": ("You are an expert insurance support agent. Your task is to answer the user's query with "
            "professionalism and accuracy, using *only* the information provided in the context. "
            "Do not infer or assume any information. If the answer is not in the context, "
            "state that you cannot find the information in their records.")},
            ]
    def _reset_message(self):
        self.messages = [
                {"role": "system", "content": ("You are an expert insurance support agent. Your task is to answer the user's query with "
            "professionalism and accuracy, using *only* the information provided in the context. "
            "Do not infer or assume any information. If the answer is not in the context, "
            "state that you cannot find the information in their records.")},
        ]
    
    def _initialize_llm(self):
        print("\nInitializing the Language Model (this may take a moment)...")
        try:
            self.llm_pipeline = pipeline(
                "text-generation",
                model="Qwen/Qwen1.5-0.5B-Chat",
                # model="Qwen/Qwen3-0.6B",
                torch_dtype="auto"
            )
            print("LLM initialized successfully!")
        except Exception as e:
            print(f"Error initializing LLM: {e}")

    def _load_data(self, data_directory):
        print("Bot is initializing and loading data...")
        try:
            for filename in os.listdir(data_directory):
                if filename.endswith('.csv'):
                    file_path = os.path.join(data_directory, filename)
                    if 'faq' in filename.lower():
                        self.faq_df = pd.read_csv(file_path).fillna('')
                    elif 'claims' in filename.lower():
                        self.claims_df = pd.read_csv(file_path, dtype={'Claim_ID': str}).fillna('')
                    elif 'policy' in filename.lower():
                        self.policy_df = pd.read_csv(file_path).fillna('')
            print("Data loading complete.")
        except FileNotFoundError:
            print(f"Error: The directory '{data_directory}' was not found.")

    def _find_id_and_data(self, query):
        
        # Patterns for IDs
        patterns = {
            'Policy_Number': r'POL\d{3}[A-Z]',
            'Customer_ID': r'CUST\d+',
            'Claim_ID': r'\b\d{4}\b'
        }

        
        for id_type, pattern in patterns.items():
            match = re.search(pattern, query.upper())
            if match:
                found_id = match.group(0)
                print(f"🔎 Found {id_type}: {found_id}")
                
                # reset the msgs if new id is found on the query
                self._reset_message()

                return found_id, id_type
        
        for id_type , pattern in patterns.items():
            match_on_msg = re.search(pattern , self.messages[-1]['content'].upper())
            if match_on_msg:
                found_id = match_on_msg.group(0)
                print(f"🔎 Found in message : {id_type}: {found_id}")
                return found_id, id_type

        return None, None

    def _lookup_context(self, found_id, id_type):
        retrieved = {}
        # Policy lookup
        if id_type == 'Policy_Number' and self.policy_df is not None:
            pol_rows = self.policy_df[self.policy_df['Policy_Number'] == found_id]
            if not pol_rows.empty:
                retrieved['policy'] = pol_rows.iloc[0].to_dict()
        # Claims lookup (for Policy or Customer or direct Claim)
        if self.claims_df is not None:
            if id_type == 'Policy_Number':
                claim_rows = self.claims_df[self.claims_df['Policy_Number'] == found_id]
            elif id_type == 'Customer_ID':
                claim_rows = self.claims_df[self.claims_df['Customer_ID'] == found_id]
            elif id_type == 'Claim_ID':
                claim_rows = self.claims_df[self.claims_df['Claim_ID'] == found_id]
            else:
                claim_rows = pd.DataFrame()
            if not claim_rows.empty:
                retrieved['claim'] = claim_rows.iloc[0].to_dict()
        print(retrieved)
        return retrieved

    def _faq_explanation(self, topic):
        if self.faq_df is not None:
            for _, row in self.faq_df.iterrows():
                if topic.lower() in str(row['Question']).lower():
                    return row['Answer']
        return None

    def answer_general_question(self, query):
        if self.faq_df is not None:
            for _, row in self.faq_df.iterrows():
                if query.lower() in str(row['Question']).lower():
                    return row['Answer']
        # return "I couldn't find a specific ID in your question or a relevant FAQ. Could you please rephrase?"
        return -1
    

    def generate_response(self, query):
        if not self.llm_pipeline:
            return "The Language Model is not available. Please check the initialization errors."
        
        general_query = self.answer_general_question(query)
        if general_query == -1:

            found_id, id_type = self._find_id_and_data(query)

            if found_id:
                context = self._lookup_context(found_id, id_type)
                # Compile all info together for LLM prompt
                
                info_lines = []
                if 'policy' in context:
                    info_lines.append("Policy Details:")
                    for k, v in context['policy'].items():
                        info_lines.append(f"{k}: {v}")
                if 'claim' in context:
                    info_lines.append("Claim Details:")
                    for k, v in context['claim'].items():
                        info_lines.append(f"{k}: {v}")
                    # FAQ context for claim remark
                    claim_remark = context['claim'].get('Remarks','') if 'claim' in context else ''
                    if claim_remark:
                        faq_expl = self._faq_explanation('claim')
                        if faq_expl:
                            info_lines.append(f"\nFAQ: {faq_expl}")
                # If we have context, ask the LLM to answer using it
                if info_lines:
                    self.messages.append({"role": "user", "content": f"Context:\n" + '\n'.join(info_lines) + f"\nQuery: {query}\nAnswer:"})
                    prompt = self.llm_pipeline.tokenizer.apply_chat_template(self.messages, tokenize=False, add_generation_prompt=True)
                    outputs = self.llm_pipeline(prompt, max_new_tokens=128, do_sample=True, temperature=0.7, top_k=50, top_p=0.95)
                    llm_answer = outputs[0]["generated_text"].split("Answer:")[1].strip()
                    return llm_answer
                # If only ID was found but no context
                else:
                    faq_response = self._faq_explanation('policy' if id_type=='Policy_Number' else 'claim')
                    return (
                        f"I recognized the {id_type.replace('_', ' ')} '{found_id}', but couldn't find any corresponding records. " +
                        (faq_response if faq_response else "")
                    )
            else:
                # return self.answer_general_question(query)
                return "I couldn't find a specific ID in your question or a relevant FAQ. Could you please rephrase?"
        else:
            return general_query

# --- Main Execution Block ---
if __name__ == "__main__":
    DATA_DIR = 'data'
    if os.path.exists(DATA_DIR):
        chatbot = InsuranceRAGChatbot(DATA_DIR)
        print("\n--- Live RAG Insurance Chatbot is Ready! ---")
        print("Ask a question containing a Claim ID, Policy Number, or Customer ID.")
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("Chatbot: Goodbye!")
                break
            response = chatbot.generate_response(user_input)
            print(f"Chatbot: {response}\n")
    else:
        print(f"Error: Please create a directory named '{DATA_DIR}' and place your CSV files inside it.")