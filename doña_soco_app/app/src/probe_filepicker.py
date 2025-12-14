# probe_filepicker.py
import flet as ft
import inspect, json

def main(page: ft.Page):
    def on_result(e: ft.FilePickerUploadEvent):
        if not e.files:
            page.add(ft.Text("No files selected"))
            return
        f = e.files[0]
        attrs = {k: (repr(getattr(f,k))[:200] if hasattr(f,k) else None) for k in dir(f) if not k.startswith('_')}
        page.add(ft.Text("File attributes:"))
        page.add(ft.Text(json.dumps(list(attrs.keys()))))
        print("DEBUG attrs:", list(attrs.keys()))
    fp = ft.FilePicker(on_result=on_result)
    page.overlay.append(fp)
    page.add(ft.Button("Pick file", on_click=lambda e: fp.pick_files()))
    
if __name__ == "__main__":
    ft.app(target=main, assets_dir="src/assets")
