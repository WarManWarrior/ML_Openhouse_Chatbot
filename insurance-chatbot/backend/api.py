import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import InsuranceRAGChatbot
from faq import ClipFaqRAG


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    type: str
    text: str


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

app = FastAPI(title="Insurance Chatbot API")

# Allow local dev frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Lazily initialized globals
chatbot: InsuranceRAGChatbot | None = None
clip_rag: ClipFaqRAG | None = None


@app.on_event("startup")
def startup_models() -> None:
    global chatbot, clip_rag
    if os.path.exists(DATA_DIR):
        chatbot = InsuranceRAGChatbot(DATA_DIR)
        try:
            clip_rag = ClipFaqRAG(DATA_DIR, faq_filename="faqs.csv")
        except Exception:
            clip_rag = None
    else:
        print(f"Warning: data directory not found at {DATA_DIR}")


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if chatbot is None:
        return ChatResponse(type="text", text="Backend not initialized. Verify data directory and model setup.")

    user_input = (req.message or "").strip()
    if not user_input:
        return ChatResponse(type="text", text="Please provide a message.")

    # Try ID-based flow first
    found_id, _ = chatbot._find_id_and_data(user_input)
    if found_id:
        answer = chatbot.generate_response(user_input)
        return ChatResponse(type="text", text=answer)

    # Fallback to FAQ semantic search via CLIP+FAISS if available
    if clip_rag is not None:
        faq_context = clip_rag.query_faqs(user_input)
        if isinstance(faq_context, dict) and chatbot.llm_pipeline:
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an expert insurance support agent. Answer using only the provided context. "
                        "If the answer is not present, say you cannot find it."
                    ),
                }
            ]
            info_lines = [
                f"Retrieved FAQ Question: {faq_context['Question']}",
                f"Retrieved FAQ Answer: {faq_context['Answer']}",
            ]
            messages.append({
                "role": "user",
                "content": "Context:\n" + "\n".join(info_lines) + f"\nQuery: {user_input}\nAnswer:",
            })
            prompt = chatbot.llm_pipeline.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            outputs = chatbot.llm_pipeline(
                prompt,
                max_new_tokens=128,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
            )
            llm_answer = outputs[0]["generated_text"].split("Answer:")[-1].strip()
            return ChatResponse(type="text", text=llm_answer)
        elif isinstance(faq_context, str):
            return ChatResponse(type="text", text=faq_context)

    # Generic fallback
    fallback = chatbot.answer_general_question(user_input)
    return ChatResponse(type="text", text=fallback)


# Convenience for local dev: uvicorn entry point
def run() -> None:
    import uvicorn

    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()


