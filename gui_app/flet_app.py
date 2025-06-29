import flet as ft
import requests
import threading
import os
import PyPDF2

MCP_URL = "http://localhost:8000"
USER_ID = "user1"

# Global state to track what file picker is currently for
file_picker_mode = None


def main(page: ft.Page):
    global file_picker_mode

    page.title = "ContextChat - Flet Version"
    page.padding = 20
    page.scroll = ft.ScrollMode.ADAPTIVE

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    chat_display = ft.TextField(
        multiline=True,
        read_only=True,
        expand=True,
    )

    user_input = ft.TextField(
        hint_text="Ask anything...",
        expand=True,
        on_submit=lambda e: send_message()
    )

    context_list = ft.ListView(expand=True, spacing=5, height=150)

    def append_message(text, color="black", end="\n"):
        chat_display.value += f"{text}{end}"
        page.run_thread(lambda: page.update())

    def refresh_context():
        try:
            r = requests.get(f"{MCP_URL}/get-context-items", params={"user_id": USER_ID})
            r.raise_for_status()
            items = r.json()
            context_list.controls.clear()
            for url in items.get("urls", []):
                context_list.controls.append(ft.Text(f"[URL] {url}"))
            for doc in items.get("documents", []):
                context_list.controls.append(ft.Text(f"[DOC] {doc}"))
            page.update()
        except:
            pass

    def send_message():
        msg = user_input.value.strip()
        if not msg:
            return
        append_message(f"You: {msg}")
        user_input.value = ""
        user_input.update()
        threading.Thread(target=stream_llama_response, args=(msg,), daemon=True).start()

    def stream_llama_response(msg):
        payload = {"user_id": USER_ID, "message": msg}
        try:
            append_message("AI: ", end="")
            with requests.post(f"{MCP_URL}/chat-stream", json=payload, stream=True) as r:
                r.raise_for_status()
                for chunk in r.iter_content(chunk_size=None):
                    if chunk:
                        token = chunk.decode("utf-8")
                        append_message(token, end="")
            append_message("")  # Final newline
        except:
            append_message("\n[Error fetching response]\n", "red")

    def add_url(e):
        url_input = ft.TextField(label="Enter URL", expand=True)

        def add_url_submit(e):
            url = url_input.value.strip()
            if url:
                try:
                    r = requests.post(f"{MCP_URL}/add-url", json={"user_id": USER_ID, "url": url})
                    if r.status_code == 200:
                        refresh_context()
                    dlg.open = False
                    page.update()
                except:
                    pass

        dlg = ft.AlertDialog(
            title=ft.Text("Add Context URL"),
            content=url_input,
            actions=[ft.TextButton("Add", on_click=add_url_submit)]
        )

        page.overlay.append(dlg)
        dlg.open = True
        page.update()


    def reset_context(e):
        try:
            r = requests.post(f"{MCP_URL}/reset-context", params={"user_id": USER_ID})
            if r.status_code == 200:
                chat_display.value = ""
                refresh_context()
        except:
            pass

    def file_picker_result(e: ft.FilePickerResultEvent):
        global file_picker_mode

        if file_picker_mode == "add_doc" and e.files:
            threading.Thread(target=process_document_task, args=(e.files[0].path,), daemon=True).start()

        elif file_picker_mode == "save_chat" and e.path:
            save_chat_to_file(e.path)

        elif file_picker_mode == "load_chat" and e.files:
            load_chat_from_file(e.files[0].path)

        file_picker_mode = None  # Reset mode after operation

    file_picker.on_result = file_picker_result

    def trigger_add_document(e):
        global file_picker_mode
        file_picker_mode = "add_doc"
        file_picker.pick_files(allow_multiple=False, allowed_extensions=["txt", "pdf"])

    def trigger_save_chat(e):
        global file_picker_mode
        file_picker_mode = "save_chat"
        file_picker.save_file(dialog_title="Save Chat History", file_name="chat.txt")

    def trigger_load_chat(e):
        global file_picker_mode
        file_picker_mode = "load_chat"
        file_picker.pick_files(dialog_title="Load Chat History", allowed_extensions=["txt"])

    def process_document_task(file_path):
        try:
            if file_path.endswith(".txt"):
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read()
            elif file_path.endswith(".pdf"):
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    text = "\n".join([page.extract_text() or "" for page in reader.pages])
            else:
                return

            payload = {"user_id": USER_ID, "document_text": text[:2000], "document_name": os.path.basename(file_path)}
            r = requests.post(f"{MCP_URL}/add-document", json=payload)
            if r.status_code == 200:
                refresh_context()
        except:
            pass

    def save_chat_to_file(path):
        if not path.endswith(".txt"):
            path += ".txt"
        with open(path, "w", encoding="utf-8") as f:
            f.write(chat_display.value)

    def load_chat_from_file(path):
        with open(path, "r", encoding="utf-8") as f:
            chat_display.value = f.read()
        page.update()

    def delete_selected_context(e):
        if not context_list.controls:
            return
        context_list.controls.pop()
        context_list.update()

    # Layout
    page.add(
        ft.Column(
            controls=[
                chat_display,
                ft.Text("Context Items:", weight=ft.FontWeight.BOLD),
                context_list,
                ft.Row([user_input, ft.IconButton(icon=ft.Icons.SEND, on_click=send_message)]),
                ft.Row([
                    ft.ElevatedButton("Add URL", on_click=add_url),
                    ft.ElevatedButton("Add Document", on_click=trigger_add_document),
                    ft.ElevatedButton("Reset Context", on_click=reset_context),
                ]),
                ft.Row([
                    ft.ElevatedButton("Save Chat", on_click=trigger_save_chat),
                    ft.ElevatedButton("Load Chat", on_click=trigger_load_chat),
                    ft.ElevatedButton("Remove Last Context", on_click=delete_selected_context),
                ])
            ],
            expand=True
        )
    )

    refresh_context()
    page.update()


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
