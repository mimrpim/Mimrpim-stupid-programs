import tkinter as tk
from tkinter import scrolledtext, messagebox, Menu
import socket
import threading
from PIL import Image, ImageTk
import json
import os

CONFIG_FILE = "server_config.json"

class ChatServerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Aetherus Server")
        self.server_socket = None
        self.clients = {}
        self.nicknames = {}
        self.debug_enabled = tk.BooleanVar()
        self.debug_enabled.set(False)
        self.running = False
        self.current_theme = "light"
        self.theme_var = tk.StringVar()

        self._load_config()
        self._create_menu()  # Call _create_menu first
        self._create_widgets()
        self._set_theme(self.current_theme)
        self._load_icon()

        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        self.menubar = Menu(self.master)  # Store the menu bar
        debugmenu = Menu(self.menubar, tearoff=0)
        debugmenu.add_checkbutton(label="Debug", variable=self.debug_enabled)

        thememenu = Menu(debugmenu, tearoff=0)
        self.theme_var.set(self.current_theme)
        thememenu.add_radiobutton(label="Světlý", variable=self.theme_var, value="light", command=self._on_theme_change)
        thememenu.add_radiobutton(label="Tmavý", variable=self.theme_var, value="dark", command=self._on_theme_change)
        debugmenu.add_cascade(label="Motiv", menu=thememenu)

        self.menubar.add_cascade(label="Nastavení", menu=debugmenu)
        self.master.config(menu=self.menubar)  # Use self.menubar

    def _debug_print(self, message):
        if self.debug_enabled.get():
            print(f"(DEBUG): {message}")

    def _create_widgets(self):
        self.notebook = tk.Frame(self.master)

        self.server_frame = tk.Frame(self.notebook)
        self.server_frame_label = tk.LabelFrame(self.notebook, text="Server")
        self.server_frame_label.pack(in_=self.notebook, side=tk.LEFT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.log_frame = tk.Frame(self.notebook)
        self.log_frame_label = tk.LabelFrame(self.notebook, text="Log")
        self.log_frame_label.pack(in_=self.notebook, side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.ip_label = tk.Label(self.server_frame_label, text="IP Adresa:")
        self.ip_label.pack(anchor=tk.W)
        self.ip_entry = tk.Entry(self.server_frame_label, width=30)
        self.ip_entry.pack(anchor=tk.W)
        self.ip_entry.insert(0, "0.0.0.0")

        self.port_label = tk.Label(self.server_frame_label, text="Port:")
        self.port_label.pack(anchor=tk.W)
        self.port_entry = tk.Entry(self.server_frame_label, width=10)
        self.port_entry.pack(anchor=tk.W)
        self.port_entry.insert(0, "2555")

        self.start_stop_button = tk.Button(self.server_frame_label, text="Spustit Server", command=self._start_server)
        self.start_stop_button.pack(pady=5, anchor=tk.W)

        self.debug_check = tk.Checkbutton(self.server_frame_label, text="Debug", variable=self.debug_enabled, command=self._toggle_debug)
        self.debug_check.pack(anchor=tk.W)

        self.log_area = scrolledtext.ScrolledText(self.log_frame_label, state=tk.DISABLED, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

    def _load_icon(self):
        """Načte a nastaví ikonu okna z PNG souboru."""
        try:
            img = Image.open("icon.png")
            self.icon_image = ImageTk.PhotoImage(img)
            self.master.iconphoto(True, self.icon_image)

        except FileNotFoundError:
            print("Soubor icon.png nebyl nalezen. Ujistěte se, že je ve stejném adresáři jako skript.")

    def _display_log(self, message):
        """Zobrazí zprávu v logovacím okně."""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.config(state=tk.DISABLED)
        self.log_area.see(tk.END)

    def _start_server(self):
        """Spustí server naslouchající na zadané IP adrese a portu."""
        if self.running:
            self._stop_server()
            return

        self.ip_address = self.ip_entry.get()
        self.port = int(self.port_entry.get())

        if not self.ip_address:
            messagebox.showerror("Chyba", "Musíte zadat IP adresu serveru.")
            return
        if not self.port:
            messagebox.showerror("Chyba", "Musíte zadat port serveru.")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind((self.ip_address, self.port))
            self.server_socket.listen(5)
            self._display_log(f"Server spuštěn na {self.ip_address}:{self.port}")
            self.running = True
            self.start_stop_button.config(text="Zastavit Server")
            threading.Thread(target=self._accept_clients, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Chyba", f"Nepodařilo se spustit server: {e}")
            self._display_log(f"Chyba při spouštění serveru: {e}")
            self.server_socket = None

    def _stop_server(self):
        """Zastaví server a odpojí všechny klienty."""
        if not self.running:
            return

        self._display_log("Zastavuji server...")
        self.running = False
        self.start_stop_button.config(text="Spustit Server")

        for client_socket in self.clients:
            try:
                client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
            except Exception as e:
                self._display_log(f"Chyba při odpojování klienta: {e}")
        self.clients.clear()
        self.nicknames.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception as e:
                self._display_log(f"Chyba při zavírání serverového socketu: {e}")
            self.server_socket = None
        self._display_log("Server zastaven.")

    def _accept_clients(self):
        """Akceptuje příchozí připojení od klientů."""
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                self._display_log(f"Připojil se klient: {client_address}")
                self.clients[client_socket] = client_address
                threading.Thread(target=self._handle_client, args=(client_socket,), daemon=True).start()
            except OSError:
                if self.running:
                    self._display_log("Chyba při akceptování klienta (server socket je pravděpodobně zavřený).")
                break
            except Exception as e:
                self._display_log(f"Chyba při akceptování klienta: {e}")
                break

    def _handle_client(self, client_socket):
        """Obsluhuje komunikaci s připojeným klientem."""
        try:
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            if not nickname:
                self._display_log(f"Klient {self.clients[client_socket]} se nepředstavil, odpojuji.")
                self._remove_client(client_socket)
                return

            if nickname in self.nicknames.values():
                self._display_log(f"Klient {self.clients[client_socket]} má duplicitní nickname '{nickname}', odpojuji.")
                client_socket.send("ERROR: Nickname je již používán.".encode('utf-8'))
                self._remove_client(client_socket)
                return

            self.nicknames[client_socket] = nickname
            self._display_log(f"Klient {self.clients[client_socket]} se představil jako '{nickname}'.")
            self._send_user_list_to_all()

            while self.running:
                try:
                    message = client_socket.recv(1024).decode('utf-8')
                    if not message:
                        self._display_log(f"Klient {self.clients[client_socket]} se odpojil.")
                        self._remove_client(client_socket)
                        break

                    if message.lower() == "/list":
                        user_list = "\n".join(self.nicknames.values())
                        self._display_log(f"Klient {self.clients[client_socket]} requested user list: {user_list}")
                        client_socket.send(f"Online uživatelé:\n{user_list}".encode('utf-8'))
                    elif message.lower() == "/cls":
                        self._display_log(f"Klient {self.clients[client_socket]} vymazal chat.")
                        self._send_message_to_all("/cls")
                    elif message.startswith("@"):
                        self._handle_private_message(client_socket, message)
                    else:
                        self._display_log(f"Přijato od {self.nicknames[client_socket]} ({self.clients[client_socket]}): {message}")
                        self._send_message_to_all(f"{self.nicknames[client_socket]}: {message}")
                except ConnectionResetError:
                    self._display_log(f"Klient {self.clients[client_socket]} se nečekaně odpojil.")
                    self._remove_client(client_socket)
                    break
                except Exception as e:
                    self._display_log(f"Chyba při komunikaci s klientem {self.clients[client_socket]}: {e}")
                    self._remove_client(client_socket)
                    break
        except Exception as e:
            self._display_log(f"Chyba při obsluze klienta {self.clients.get(client_socket, 'Neznámý')}: {e}")
            self._remove_client(client_socket)

    def _handle_private_message(self, client_socket, message):
        """Obslouží soukromou zprávu."""
        parts = message.split(" ", 1)
        if len(parts) > 1:
            recipient_nick = parts[0][1:]
            content = parts[1]
            recipient_socket = None
            for sock, nick in self.nicknames.items():
                if nick == recipient_nick:
                    recipient_socket = sock
                    break
            if recipient_socket:
                sender_nick = self.nicknames[client_socket]
                try:
                    recipient_socket.send(f"(Soukromá zpráva od {sender_nick}): {content}".encode('utf-8'))
                    client_socket.send(f"(Soukromá zpráva pro {recipient_nick}): {content}".encode('utf-8'))
                    self._display_log(f"(Soukromá zpráva) {sender_nick} -> {recipient_nick}: {content}")
                except Exception as e:
                    self._display_log(f"Chyba při odesílání soukromé zprávy: {e}")
            else:
                self._display_log(f"Klient {self.clients[client_socket]} se pokusil poslat soukromou zprávu uživateli '{recipient_nick}', který není online.")
                client_socket.send("ERROR: Uživatel není online.".encode('utf-8'))

    def _send_message_to_all(self, message):
        """Odešle zprávu všem připojeným klientům."""
        if self.debug_enabled.get():
            self._display_log(f"Odesílám všem: {message}")
        for client_socket in self.clients:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                self._display_log(f"Chyba při odesílání zprávy klientovi: {e}")

    def _send_user_list_to_all(self):
        """Odešle seznam online uživatelů všem připojeným klientům."""
        users_list = "\n".join(self.nicknames.values())
        message = f"§{users_list}"
        if self.debug_enabled.get():
            self._display_log(f"Odesílám seznam uživatelů všem: {message}")
        for client_socket in self.clients:
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as e:
                self._display_log(f"Chyba při odesílání seznamu uživatelů klientovi: {e}")

    def _remove_client(self, client_socket):
        """Odstraní klienta ze seznamu připojených klientů."""
        client_address = self.clients.get(client_socket)
        if client_address:
            self._display_log(f"Odpojuji klienta: {client_address}")
        if client_socket in self.nicknames:
            nickname = self.nicknames[client_socket]
            del self.nicknames[client_socket]
            self._send_user_list_to_all()
        if client_socket in self.clients:
            del self.clients[client_socket]
        try:
            client_socket.close()
        except Exception as e:
            self._display_log(f"Chyba při zavírání soketu klienta: {e}")

    def _on_closing(self):
        """Obsluha události při zavírání okna serveru."""
        self._stop_server()
        self.master.destroy()

    def _toggle_debug(self):
        """Zapne nebo vypne debug režim."""
        if self.debug_enabled.get():
            self._display_log("Debug režim zapnut.")
        else:
            self._display_log("Debug režim vypnut.")

    def _set_theme(self, theme):
        """Nastaví vizuální styl aplikace na základě zvoleného motivu."""
        if theme == "dark":
            self.master.config(bg="#212121")
            self.log_area.config(bg="#2a2a2a", fg="#eeeeee", insertbackground="#ffffff")
            if hasattr(self, 'ip_label'):
                self.ip_label.config(fg="#eeeeee")
            if hasattr(self, 'port_label'):
                self.port_label.config(fg="#eeeeee")
            if hasattr(self, 'start_stop_button'):
                self.start_stop_button.config(bg="#212121", fg="#ffffff", activebackground="#4CAF50", activeforeground="#ffffff")
            if hasattr(self, 'debug_check'):
                self.debug_check.config(fg="#eeeeee")
            if hasattr(self, 'server_frame_label'):
                self.server_frame_label.config(bg="#2a2a2a", fg="#eeeeee", highlightbackground="#2a2a2a", highlightcolor="#2a2a2a", bd=0)
            if hasattr(self, 'log_frame_label'):
                self.log_frame_label.config(bg="#2a2a2a", fg="#eeeeee", highlightbackground="#2a2a2a", highlightcolor="#2a2a2a", bd=0)
        elif theme == "light":
            self.master.config(bg="#ffffff")
            self.log_area.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
            if hasattr(self, 'ip_label'):
                self.ip_label.config(fg="#000000")
            if hasattr(self, 'port_label'):
                self.port_label.config(fg="#000000")
            if hasattr(self, 'start_stop_button'):
                self.start_stop_button.config(bg="#4CAF50", fg="#ffffff", activebackground="#66BB6A", activeforeground="#ffffff")
            if hasattr(self, 'debug_check'):
                self.debug_check.config(fg="#000000")
            if hasattr(self, 'server_frame_label'):
                self.server_frame_label.config(bg="#f0f0f0", fg="#000000", highlightbackground="#f0f0f0", highlightcolor="#f0f0f0", bd=0)
            if hasattr(self, 'log_frame_label'):
                self.log_frame_label.config(bg="#f0f0f0", fg="#000000", highlightbackground="#f0f0f0", highlightcolor="#f0f0f0", bd=0)
        self.current_theme = theme

    def _on_theme_change(self):
        selected_theme = self.theme_var.get()
        self._set_theme(selected_theme)
        self._save_config()

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.current_theme = config.get("theme", "light")
            except (json.JSONDecodeError, KeyError):
                print("Chyba při načítání konfigurace. Používám výchozí nastavení.")
                self._save_config()

    def _save_config(self):
        config = {
            "theme": self.current_theme,
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Chyba při ukládání konfigurace: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    server_gui = ChatServerGUI(root)
    root.mainloop()
