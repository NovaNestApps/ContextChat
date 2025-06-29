from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from crawler import extract_text_from_url
from context_store import context_data
from fastapi import Query
from fastapi.responses import StreamingResponse
import json

app = FastAPI()
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"


class ChatRequest(BaseModel):
    user_id: str
    message: str


class UrlRequest(BaseModel):
    user_id: str
    url: str


@app.post("/chat")
def chat(req: ChatRequest):
    user_context = context_data.get(req.user_id, {})
    history = user_context.get("history", "")
    url_text = user_context.get("url_text", "")

    full_prompt = f"{url_text}\n{history}\nUser: {req.message}\nAI:"

    payload = {"model": MODEL_NAME, "prompt": full_prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code == 200:
        result = response.json().get("response", "").strip()

        # Update chat history
        updated_history = f"{history}\nUser: {req.message}\nAI: {result}"

        # Limit history to last 3000 chars for safety
        updated_history = updated_history[-3000:]

        context_data[req.user_id] = {
            "history": updated_history,
            "urls": user_context.get("urls", []),
            "url_text": url_text
        }

        return {"response": result}
    else:
        raise HTTPException(status_code=500, detail="LLM error")




MAX_URLS = 3  # Limit to 3 URLs for MVP

@app.post("/add-url")
def add_url(req: UrlRequest):
    user_context = context_data.get(req.user_id, {"history": "", "urls": [], "url_text": ""})

    if req.url in user_context["urls"]:
        raise HTTPException(status_code=400, detail="URL already added.")

    text = extract_text_from_url(req.url)
    if not text:
        raise HTTPException(status_code=400, detail="Failed to fetch URL content")

    user_context["urls"].append(req.url)
    user_context["url_text"] += f"\nContext from {req.url}:\n{text}"

    # Optional: limit total url_text size
    if len(user_context["url_text"]) > 5000:
        user_context["url_text"] = user_context["url_text"][-5000:]

    context_data[req.user_id] = user_context
    return {"message": "URL added and context updated"}

@app.get("/get-context-items")
def get_context_items(user_id: str = Query(...)):
    user_context = context_data.get(user_id, {})
    return {
        "urls": user_context.get("urls", []),
        "documents": [doc["name"] for doc in user_context.get("documents", [])]
    }

@app.post("/remove-url")
def remove_url(req: UrlRequest):
    user_context = context_data.get(req.user_id, {})
    urls = user_context.get("urls", [])
    url_text = user_context.get("url_text", "")

    if req.url not in urls:
        raise HTTPException(status_code=400, detail="URL not found.")

    # Remove URL from list
    urls.remove(req.url)

    # Rebuild url_text from remaining URLs
    combined_text = ""
    for u in urls:
        combined_text += f"\nContext from {u}:\n{extract_text_from_url(u)}"

    # Update context
    user_context["urls"] = urls
    user_context["url_text"] = combined_text
    context_data[req.user_id] = user_context

    return {"message": "URL removed and context updated"}

@app.post("/reset-context")
def reset_context(user_id: str = Query(...)):
    context_data.pop(user_id, None)
    return {"message": "Context reset"}

@app.post("/chat-stream")
def chat_stream(req: ChatRequest):
    user_context = context_data.get(req.user_id, {})
    history = user_context.get("history", "")
    url_text = user_context.get("url_text", "")

    full_prompt = f"{url_text}\n{history}\nUser: {req.message}\nAI:"

    payload = {"model": MODEL_NAME, "prompt": full_prompt, "stream": True}
    response = requests.post(OLLAMA_URL, json=payload, stream=True)

    def generate():
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                token = data.get("response", "")
                yield token

    return StreamingResponse(generate(), media_type="text/plain")

class DocumentRequest(BaseModel):
    user_id: str
    document_text: str
    document_name: str


@app.post("/add-document")
def add_document(req: DocumentRequest):
    user_context = context_data.get(req.user_id, {"history": "", "urls": [], "documents": [], "url_text": ""})

    user_context["documents"].append({"name": req.document_name, "text": req.document_text})
    user_context["url_text"] += f"\nContext from document ({req.document_name}):\n{req.document_text}"

    if len(user_context["url_text"]) > 5000:
        user_context["url_text"] = user_context["url_text"][-5000:]

    context_data[req.user_id] = user_context
    return {"message": "Document context added"}

class DocumentRemoveRequest(BaseModel):
    user_id: str
    document_name: str


@app.post("/remove-document")
def remove_document(req: DocumentRemoveRequest):
    user_context = context_data.get(req.user_id, {})
    documents = user_context.get("documents", [])
    url_text = user_context.get("url_text", "")

    doc_to_remove = next((d for d in documents if d["name"] == req.document_name), None)
    if not doc_to_remove:
        raise HTTPException(status_code=400, detail="Document not found.")

    documents.remove(doc_to_remove)

    # Rebuild url_text from remaining URLs and Documents
    combined_text = ""
    for u in user_context.get("urls", []):
        combined_text += f"\nContext from {u}:\n{extract_text_from_url(u)}"
    for d in documents:
        combined_text += f"\nContext from document ({d['name']}):\n{d['text']}"

    user_context["documents"] = documents
    user_context["url_text"] = combined_text
    context_data[req.user_id] = user_context

    return {"message": "Document removed and context updated"}
