import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import requests
import threading
from tkinter import filedialog

MCP_URL = "http://localhost:8000"
USER_ID = "user1"


def send_message():
    message = input_field.get()
    if not message or message == "Ask anything":
        return
    input_field.delete(0, tk.END)
    input_field.config(state=tk.DISABLED)

    chat_display.insert(tk.END, "You: ", "user_label")
    chat_display.insert(tk.END, f"{message}\n\n", "user_msg")
    chat_display.insert(tk.END, "AI: (thinking...)\n\n", "ai_thinking")
    chat_display.see(tk.END)
    threading.Thread(target=fetch_llama_response, args=(message,), daemon=True).start()



def fetch_llama_response(message):
    payload = {"user_id": USER_ID, "message": message}
    try:
        response = requests.post(f"{MCP_URL}/chat", json=payload)
        reply = response.json().get("response", "")
    except Exception as e:
        reply = f"Error: {e}"

    root.after(0, lambda: update_ai_response(reply))


def update_ai_response(response_text):
    # Remove "(thinking...)" line
    chat_display.delete("end-3l", "end-2l")

    chat_display.insert(tk.END, "AI: ", "ai_label")
    chat_display.insert(tk.END, f"{response_text}\n\n", "ai_response")
    chat_display.see(tk.END)
    input_field.config(state=tk.NORMAL)
    input_field.focus_set()


def add_url():
    url = simpledialog.askstring("Add URL", "Enter URL to fetch context:")
    if not url:
        return

    payload = {"user_id": USER_ID, "url": url}
    try:
        response = requests.post(f"{MCP_URL}/add-url", json=payload)
        if response.status_code == 200:
            messagebox.showinfo("Success", "URL added.")
            refresh_urls()
        else:
            messagebox.showerror("Error", f"{response.status_code} - {response.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def refresh_urls():
    try:
        response = requests.get(f"{MCP_URL}/get-urls", params={"user_id": USER_ID})
        if response.status_code == 200:
            urls = response.json().get("urls", [])
            urls_listbox.delete(0, tk.END)
            for u in urls:
                urls_listbox.insert(tk.END, u)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch URLs: {e}")

def delete_selected_url():
    selected = urls_listbox.curselection()
    if not selected:
        messagebox.showwarning("Warning", "Please select a URL to delete.")
        return

    url = urls_listbox.get(selected[0])
    payload = {"user_id": USER_ID, "url": url}
    try:
        response = requests.post(f"{MCP_URL}/remove-url", json=payload)
        if response.status_code == 200:
            messagebox.showinfo("Success", "URL removed.")
            refresh_urls()
        else:
            messagebox.showerror("Error", f"{response.status_code} - {response.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def reset_context():
    confirm = messagebox.askyesno("Reset Context", "Are you sure you want to clear all context and URLs?")
    if not confirm:
        return

    try:
        response = requests.post(f"{MCP_URL}/reset-context", params={"user_id": USER_ID})
        if response.status_code == 200:
            chat_display.delete(1.0, tk.END)
            urls_listbox.delete(0, tk.END)
            messagebox.showinfo("Success", "Context cleared.")
        else:
            messagebox.showerror("Error", f"{response.status_code} - {response.text}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def save_chat():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if not file_path:
        return

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(chat_display.get(1.0, tk.END))
        messagebox.showinfo("Success", "Chat saved successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save chat: {e}")


def load_chat():
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
    if not file_path:
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        chat_display.delete(1.0, tk.END)
        chat_display.insert(tk.END, content)
        messagebox.showinfo("Success", "Chat loaded successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load chat: {e}")

# Root window setup
root = tk.Tk()
root.title("ContextChat")
root.geometry("650x550")

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
chat_display.tag_configure("user_label", foreground="white", font=("Arial", 12, "bold"))
chat_display.tag_configure("user_msg", foreground="white")
chat_display.tag_configure("ai_label", foreground="green", font=("Arial", 12, "bold"))
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

input_field.focus_set()

# URLs Display Frame
urls_frame = tk.Frame(root)
urls_frame.pack(fill=tk.BOTH, padx=10, pady=5)

urls_label = tk.Label(urls_frame, text="Added URLs:", font=("Arial", 11, "bold"))
urls_label.pack(anchor=tk.W)

urls_listbox = tk.Listbox(urls_frame, height=3)
urls_listbox.pack(fill=tk.BOTH, expand=True)

delete_button = tk.Button(urls_frame, text="Remove Selected URL", command=delete_selected_url)
delete_button.pack(pady=2, anchor=tk.E)

reset_button = tk.Button(top_frame, text="Reset Context", command=reset_context)
reset_button.pack(side=tk.RIGHT, padx=(5, 0))

file_buttons_frame = tk.Frame(root)
file_buttons_frame.pack(fill=tk.X, padx=10, pady=5)

save_button = tk.Button(file_buttons_frame, text="Save Chat", command=save_chat)
save_button.pack(side=tk.LEFT)

load_button = tk.Button(file_buttons_frame, text="Load Chat", command=load_chat)
load_button.pack(side=tk.LEFT, padx=(5, 0))


root.mainloop()
