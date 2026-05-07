import os
import sys
import json
import threading
import webbrowser
import winreg
import subprocess
import requests
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item

from werkzeug.serving import make_server
from app import app, init_db

APP_VERSION = "1.0.0"
GITHUB_REPO = "theXstudent/Fatoora-updates"

appdata_dir = os.environ.get('APPDATA', os.path.expanduser('~'))
fatoora_data_dir = os.path.join(appdata_dir, 'FatooraApp')
if not os.path.exists(fatoora_data_dir):
    os.makedirs(fatoora_data_dir, exist_ok=True)

CONFIG_FILE = os.path.join(fatoora_data_dir, 'fatoora_settings.json')

class ServerThread(threading.Thread):
    def __init__(self, app, port):
        threading.Thread.__init__(self)
        self.server = make_server('127.0.0.1', port, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

server_thread = None
current_port = 5000

def load_port():
    global current_port
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                current_port = data.get('port', 5000)
        except:
            pass
    return current_port

def save_port(port):
    with open(CONFIG_FILE, 'w') as f:
        json.dump({'port': port}, f)

def start_server(port):
    global server_thread
    if server_thread:
        server_thread.shutdown()
        server_thread.join()
    
    server_thread = ServerThread(app, port)
    server_thread.daemon = True
    server_thread.start()

def restart_server(new_port):
    global current_port
    current_port = new_port
    start_server(new_port)

def add_to_startup():
    if not getattr(sys, 'frozen', False):
        return
        
    exe_path = sys.executable
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    app_name = "FatooraApp"
    
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Startup error: {e}")

def create_image():
    # Simple blue square with a white square inside for the tray icon
    image = Image.new('RGB', (64, 64), color=(37, 99, 235))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(255, 255, 255))
    return image

def launch_browser(icon, item):
    webbrowser.open(f"http://127.0.0.1:{current_port}")

def edit_port(icon, item):
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    new_port = simpledialog.askinteger("Port", "Entrez le nouveau port:", initialvalue=current_port)
    root.destroy()
    if new_port and new_port != current_port:
        save_port(new_port)
        restart_server(new_port)

def check_for_updates(icon, item):
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    try:
        response = requests.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest")
        response.raise_for_status()
        data = response.json()
        latest_version = data.get("tag_name", "").lstrip("v")
        
        if latest_version > APP_VERSION:
            msg = f"Une nouvelle version ({latest_version}) est disponible. Voulez-vous la télécharger et l'installer ?"
            if messagebox.askyesno("Mise à jour disponible", msg):
                assets = data.get("assets", [])
                exe_url = None
                for asset in assets:
                    if asset["name"].endswith(".exe"):
                        exe_url = asset["browser_download_url"]
                        break
                
                if exe_url:
                    # Download the exe
                    import tempfile
                    temp_dir = tempfile.gettempdir()
                    new_exe_path = os.path.join(temp_dir, "fatoora_update.exe")
                    
                    r = requests.get(exe_url, stream=True)
                    with open(new_exe_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if getattr(sys, 'frozen', False):
                        current_exe = sys.executable
                        # Create bat file to replace
                        bat_path = os.path.join(temp_dir, "updater.bat")
                        with open(bat_path, "w") as bat_file:
                            bat_file.write(f'''@echo off
timeout /t 2 /nobreak > NUL
move /Y "{new_exe_path}" "{current_exe}"
start "" "{current_exe}"
del "%~f0"
''')
                        subprocess.Popen([bat_path], shell=True)
                        exit_app(icon, item)
                    else:
                        messagebox.showinfo("Mise à jour", "Téléchargé ! Remplacez manuellement le fichier .exe.")
                else:
                    messagebox.showerror("Erreur", "Aucun fichier .exe trouvé dans la release.")
        else:
            messagebox.showinfo("À jour", "Vous avez déjà la dernière version.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible de vérifier les mises à jour : {e}")
    finally:
        root.destroy()

def uninstall_app(icon, item):
    root = tk.Tk()
    root.attributes("-topmost", True)
    root.withdraw()
    if messagebox.askyesno("Désinstaller", "Êtes-vous sûr de vouloir désinstaller Fatoora et supprimer toutes les données ?"):
        try:
            # Remove from startup
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
                winreg.DeleteValue(key, "FatooraApp")
                winreg.CloseKey(key)
            except:
                pass
            
            if getattr(sys, 'frozen', False):
                import tempfile
                temp_dir = tempfile.gettempdir()
                bat_path = os.path.join(temp_dir, "uninstall.bat")
                current_exe = sys.executable
                with open(bat_path, "w") as bat_file:
                    bat_file.write(f'''@echo off
timeout /t 2 /nobreak > NUL
del "{current_exe}"
rmdir /s /q "{fatoora_data_dir}"
del "%~f0"
''')
                subprocess.Popen([bat_path], shell=True)
                exit_app(icon, item)
            else:
                import shutil
                shutil.rmtree(fatoora_data_dir, ignore_errors=True)
                exit_app(icon, item)
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la désinstallation : {e}")
    root.destroy()

def exit_app(icon, item):
    if server_thread:
        server_thread.shutdown()
    icon.stop()

def main():
    add_to_startup()
    init_db()
    load_port()
    start_server(current_port)

    menu = pystray.Menu(
        item('Lancer (Navigateur)', launch_browser, default=True),
        item('Modifier le port', edit_port),
        item('Vérifier les mises à jour', check_for_updates),
        pystray.Menu.SEPARATOR,
        item('Désinstaller', uninstall_app),
        pystray.Menu.SEPARATOR,
        item('Quitter', exit_app)
    )
    
    icon = pystray.Icon("Fatoora", create_image(), "Fatoora Web App", menu)
    icon.run()

if __name__ == '__main__':
    main()
