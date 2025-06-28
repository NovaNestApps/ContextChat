import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import requests
import threading


MCP_URL = "http://localhost:8000"  # Adjust if needed
USER_ID = "user1"  # Static for MVP


def send_message():
    message = input_field.get()
    if not message or message == "Ask anything":
        return

    chat_display.insert(tk.END, f"You: {message}\n\n")
    chat_display.insert(tk.END, "AI: (thinking...)\n", "ai_thinking")
    chat_display.see(tk.END)
    input_field.delete(0, tk.END)

    # Call LLaMA in background thread
    threading.Thread(target=fetch_llama_response, args=(message,), daemon=True).start()



def add_url():
    url = simpledialog.askstring("Add URL", "Enter URL to fetch context:")
    if not url:
        return

    payload = {"user_id": USER_ID, "url": url}
    try:
        response = requests.post(f"{MCP_URL}/add-url", json=payload)
        if response.status_code == 200:
            messagebox.showinfo("Success", "URL added.")
        else:
            messagebox.showerror("Error", f"{response.status_code} - {response.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def fetch_llama_response(message):
    payload = {"user_id": USER_ID, "message": message}
    try:
        response = requests.post(f"{MCP_URL}/chat", json=payload)
        reply = response.json().get("response", "")
    except Exception as e:
        reply = f"Error: {e}"

    chat_display.insert(tk.END, "AI: (thinking...)\n", "ai_thinking")
    chat_display.see(tk.END)
    root.after(500, lambda: update_ai_response(reply))


def update_ai_response(response_text):
    # Delete the temporary "(thinking...)" line
    chat_display.delete("end-3l", "end-2l")

    # Add formatted AI response
    chat_display.insert(tk.END, f"AI: {response_text}\n\n", "ai_response")
    chat_display.see(tk.END)


# Root window setup
root = tk.Tk()
root.title("ContextChat")
root.geometry("600x500")

font_main = ("Arial", 12)

# Top Frame for URL Button
top_frame = tk.Frame(root)
top_frame.pack(fill=tk.X, padx=10, pady=5)

spacer = tk.Label(top_frame, text="")
spacer.pack(side=tk.LEFT, expand=True)

url_button = tk.Button(top_frame, text="Add URL for Context", command=add_url)
url_button.pack(side=tk.RIGHT)

# Chat Display
chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=font_main)
chat_display.tag_configure("ai_response", foreground="green")
chat_display.tag_configure("ai_thinking", foreground="gray", font=("Arial", 10, "italic"))
chat_display.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

# Input Frame
input_frame = tk.Frame(root)
input_frame.pack(fill=tk.X, padx=10, pady=5)

input_field = tk.Entry(input_frame, font=font_main)
input_field.insert(0, "Ask anything")
input_field.bind("<FocusIn>", lambda event: input_field.delete(0, tk.END) if input_field.get() == "Ask anything" else None)
input_field.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
input_field.bind("<Return>", lambda event: send_message())

send_button = tk.Button(input_frame, text="Send", command=send_message)
send_button.pack(side=tk.RIGHT)

root.mainloop()