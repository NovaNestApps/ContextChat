
# ContextChat - Local AI Chat with Web Context

**ContextChat** is a fully local, privacy-respecting AI chat application powered by open-source LLMs (like LLaMA via Ollama). It enhances chat responses by integrating context from user-defined web pages, all running entirely on your machine.

## Features (Current MVP)

✔ Local desktop chat app with clean, simple UI.  
✔ Sends messages to a local MCP (Message/Context/Prompt) server.  
✔ MCP server manages conversation history and context.  
✔ Users can add URLs — MCP extracts content and feeds it to the LLM.  
✔ LLM responses via Ollama using GGUF models (e.g., LLaMA, Mistral).  
✔ No internet required after setup — fully private, local inference.  


## Getting Started

### 1. **Install Ollama**

Follow [https://ollama.com/download](https://ollama.com/download) for Mac or Linux.

Example for Linux:

```
curl -fsSL https://ollama.com/install.sh | sh
```

Run:

```
ollama serve
ollama pull mistral  # Or your preferred model
```

### 2. **Set Up MCP Server**

In `mcp_server` folder:

```
pip install -r requirements.txt
uvicorn main:app --reload
```

### 3. **Run GUI Chat App**

In `gui_app` folder:

```
pip install -r requirements.txt
python app.py
```


## Project Structure

```
contextchat/
├── mcp_server/      # FastAPI MCP server (context, crawling, LLM integration)
├── gui_app/         # Tkinter desktop chat application
└── README.md
```

## How It Works

1. You chat via the GUI.  
2. Message goes to MCP server.  
3. MCP fetches relevant context (URLs you added, conversation history).  
4. MCP sends a combined prompt to Ollama.  
5. LLM generates a response, displayed in the GUI.  

## Requirements

- Python 3.9+  
- Ollama installed locally  
- Internet only needed to pull models initially  

## Planned Future Development

- [ ] Show added URLs directly in the GUI.  
- [ ] GUI button to clear/reset context.  
- [ ] Save and load chat history to/from files.  
- [ ] Visual theme improvements (color scheme, fonts, layouts).  
- [ ] Streaming LLM responses for real-time chat feel.  
- [ ] Switch to Flet or PyQt for modern GUI experience (optional).  
- [ ] Support document (PDF, TXT) ingestion as context.  
- [ ] Advanced crawler with JavaScript rendering (Playwright integration).  
- [ ] Easy packaging for Mac/Linux as standalone desktop app.  
- [ ] Open-source community contributions welcome.  

## Why Local?

✔ Full privacy — no data leaves your machine.  
✔ No reliance on cloud AI APIs.  
✔ Fast, responsive LLM inference with no network delay.  
✔ Ideal for researchers, developers, privacy-conscious users.  

## Contributing

This is an evolving open-source project. Pull requests, suggestions, and issue reports are welcome!


## Disclaimer

This is a work-in-progress prototype. Expect rough edges and active development.  

**Enjoy your private AI chat experience!**
