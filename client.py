import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, Menu, ttk
import socket
import threading
from PIL import Image, ImageTk  # Importujeme PIL pro práci s obrázky
import json  # Importujeme modul json pro práci s konfiguračním souborem
import os # Import modul os

SERVER_PORT = 2555
CONFIG_FILE = "config.json"  # Název konfiguračního souboru

class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Aetherus Chat")
        self.nickname = None
        self.client_socket = None
        self.debug_enabled = tk.BooleanVar()
        self.debug_enabled.set(False)
        self.server_ip = None
        self.server_port = None
        self.current_theme = "light"  # Výchozí motiv
        self.theme_var = tk.StringVar()  # Proměnná pro ukládání aktuálního motivu

        self._create_menu()
        self._create_widgets()
        self._set_theme(self.current_theme)  # Nastavíme motiv podle načtené konfigurace
        self._load_icon()
        self._load_config()  # Načteme konfiguraci po vytvoření widgetů

        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        menubar = Menu(self.master)
        debugmenu = Menu(menubar, tearoff=0)
        debugmenu.add_checkbutton(label="Debug", variable=self.debug_enabled)

        # Vytvoříme submenu pro výběr motivu v menu Nastavení
        thememenu = Menu(debugmenu, tearoff=0)
        # Použijeme StringVar pro propojení s Radiobuttony
        self.theme_var.set(self.current_theme)  # Nastavíme výchozí hodnotu
        thememenu.add_radiobutton(label="Světlý", variable=self.theme_var, value="light", command=self._on_theme_change)
        thememenu.add_radiobutton(label="Tmavý", variable=self.theme_var, value="dark", command=self._on_theme_change)
        debugmenu.add_cascade(label="Motiv", menu=thememenu)  # Přidáme submenu "Motiv" do menu "Nastavení"

        menubar.add_cascade(label="Nastavení", menu=debugmenu)
        self.master.config(menu=menubar)

    def _debug_print(self, message):
        if self.debug_enabled.get():
            print(f"(DEBUG): {message}")

    def _create_widgets(self):
        self.connect_frame = tk.Frame(self.master)
        self.connect_frame.pack(pady=10)

        self.server_label = tk.Label(self.connect_frame, text="Vyber Server:")
        self.server_label.pack(side=tk.LEFT)

        self.server_combobox = ttk.Combobox(
            self.connect_frame,
            values=["cz.aetherus.mbservers.fun", "en.aetherus.mbservers.fun", "sk.aetherus.mbservers.fun", "custom"],
            state="readonly",
            width=25
        )
        self.server_combobox.pack(side=tk.LEFT, padx=5)
        self.server_combobox.set("cz.aetherus.mbservers.fun")

        self.custom_ip_label = tk.Label(self.connect_frame, text="Vlastní IP:")
        self.custom_ip_label.pack(side=tk.LEFT)
        self.custom_ip_entry = tk.Entry(self.connect_frame)
        self.custom_ip_entry.pack(side=tk.LEFT)
        self.custom_ip_label.pack_forget()
        self.custom_ip_entry.pack_forget()

        self.custom_port_label = tk.Label(self.connect_frame, text="Port:")
        self.custom_port_label.pack(side=tk.LEFT, padx=5)
        self.custom_port_entry = tk.Entry(self.connect_frame, width=5)
        self.custom_port_entry.insert(0, str(SERVER_PORT))
        self.custom_port_entry.pack(side=tk.LEFT)
        self.custom_port_label.pack_forget()
        self.custom_port_entry.pack_forget()

        self.server_combobox.bind("<<ComboboxSelected>>", self._on_server_select)

        self.connect_button = tk.Button(self.connect_frame, text="Připojit", command=self._connect_to_server)
        self.connect_button.pack(side=tk.LEFT, padx=10)

        self.chat_area = scrolledtext.ScrolledText(self.master, state=tk.DISABLED)
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_frame = tk.Frame(self.master)
        self.message_frame.pack(padx=10, pady=5, fill=tk.X)

        self.message_entry = tk.Entry(self.message_frame)
        self.message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.message_entry.bind("<Return>", self._send_message)

        self.send_button = tk.Button(self.message_frame, text="Odeslat", command=self._send_message)
        self.send_button.pack(side=tk.RIGHT, padx=5)

        self.online_list_label = tk.Label(self.master, text="Online Uživatelé:")
        self.online_list_label.pack(padx=10, pady=(5, 0), anchor=tk.W)

        self.online_list = tk.Listbox(self.master, height=5)
        self.online_list.pack(padx=10, pady=(0, 10), fill=tk.BOTH)
        self.online_list.bind("<Double-Button-1>", self._start_private_message)

    def _load_icon(self):
        """Načte a nastaví ikonu okna z PNG souboru."""
        try:
            img = Image.open("icon.png")
            self.icon_image = ImageTk.PhotoImage(img)
            self.master.iconphoto(True, self.icon_image)

        except FileNotFoundError:
            print("Soubor icon.png nebyl nalezen. Ujistěte se, že je ve stejném adresáři jako skript.")

    def _on_server_select(self, event):
        selected_server = self.server_combobox.get()
        if selected_server == "custom":
            self.custom_ip_label.pack(side=tk.LEFT)
            self.custom_ip_entry.pack(side=tk.LEFT)
            self.custom_port_label.pack(side=tk.LEFT, padx=5)
            self.custom_port_entry.pack(side=tk.LEFT)
        else:
            self.custom_ip_label.pack_forget()
            self.custom_ip_entry.pack_forget()
            self.custom_port_label.pack_forget()
            self.custom_port_entry.pack_forget()

    def _connect_to_server(self):
        """Připojí se k vybranému serveru."""
        selected_server = self.server_combobox.get()
        if selected_server == "custom":
            server_ip = self.custom_ip_entry.get()
            server_port = int(self.custom_port_entry.get())
            if not server_ip:
                messagebox.showerror("Chyba", "Musíte zadat IP adresu vlastního serveru.")
                return
        else:
            server_ip = selected_server
            server_port = SERVER_PORT

        self.server_ip = server_ip
        self.server_port = server_port
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.server_ip, self.server_port))
            self._display_message(f"Připojeno k serveru na {self.server_ip}:{self.server_port}\n")
            self.connect_button.config(state=tk.DISABLED)

            nickname = simpledialog.askstring("Nickname", "Zadejte svůj nickname:", parent=self.master)
            if nickname:
                self.nickname = nickname
                self.client_socket.send(self.nickname.encode('utf-8'))
                threading.Thread(target=self._receive_messages, daemon=True).start()
            else:
                self._disconnect()
        except ConnectionRefusedError:
            messagebox.showerror("Chyba", f"Nelze se připojit k serveru na {self.server_ip}:{self.server_port}. Ujistěte se, že server běží.")
        except socket.error as e:
            messagebox.showerror("Chyba", f"Chyba připojení: {e}")

    def _receive_messages(self):
        while self.client_socket:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("§"):
                    self._update_online_users(message)
                elif message.strip() == "/cls":  # Přidána podmínka pro vymazání chatu
                    self._clear_chat()
                else:
                    self._display_message(message)
            except ConnectionAbortedError:
                self._display_message("Připojení k serveru bylo přerušeno.\n")
                break
            except ConnectionResetError:
                self._display_message("Server ukončil spojení.\n")
                break
            except Exception as e:
                print(f"Chyba při příjmu zpráv: {e}")
                break
        self._disconnect()

    def _display_message(self, message):
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.insert(tk.END, message + "\n")
        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)

    def _clear_chat(self):
        """Vymaže obsah chatovacího okna."""
        self.chat_area.config(state=tk.NORMAL)
        self.chat_area.delete("1.0", tk.END)
        self.chat_area.config(state=tk.DISABLED)

    def _send_message(self, event=None):
        message = self.message_entry.get()
        if message:
            if message.startswith("@"):
                parts = message.split(" ", 1)
                if len(parts) == 2:
                    recipient_nick = parts[0][1:]
                    content = parts[1]
                    self.client_socket.send(f"{recipient_nick}: {content}".encode('utf-8'))
                    self._display_message(f"(Já -> {recipient_nick} (soukromě)): {content}")
                else:
                    self._display_message("Chyba: Nesprávný formát soukromé zprávy. Použijte @nickname zpráva")
            else:
                self.client_socket.send(message.encode('utf-8'))
                self._display_message(f"(Já): {message}")
            self.message_entry.delete(0, tk.END)

    def _update_online_users(self, message):
        self._debug_print(f"Přijatá zpráva o online uživatelích (označená): '{message}'")
        self.online_list.delete(0, tk.END)
        if message.startswith("§"):
            users_str = message[1:].strip()
            if users_str:
                users = users_str.split("\n")
                self._debug_print(f"Seznam uživatelů po rozdělení (označený): '{users}'")
                for user in users:
                    if user and user != self.nickname:
                        self._debug_print(f"Pokus o vložení do listboxu (označený): '{user}'")
                        self.online_list.insert(tk.END, user)
            else:
                self._debug_print("Seznam online uživatelů (označený) je prázdný.")
        else:
            self._debug_print("Přijatá zpráva o online uživatelích (označená) nemá očekávaný formát.")

    def _start_private_message(self, event):
        selected_user = self.online_list.get(tk.ANCHOR)
        if selected_user:
            self.message_entry.delete(0, tk.END)
            self.message_entry.insert(0, f"@{selected_user} ")

    def _disconnect(self):
        if self.client_socket:
            self.client_socket.close()
            self.client_socket = None
            self._display_message("Odpojeno od serveru.\n")
            self.connect_button.config(state=tk.NORMAL)

    def _on_closing(self):
        self._disconnect()
        self.master.destroy()

    def _set_theme(self, theme):
        """Nastaví vizuální styl aplikace na základě zvoleného motivu."""
        if theme == "dark":
            self.master.config(bg="#212121")
            self.chat_area.config(bg="#2a2a2a", fg="#eeeeee", insertbackground="#ffffff", state=tk.DISABLED)
            self.message_entry.config(bg="#2a2a2a", fg="#eeeeee", insertbackground="#ffffff")
            self.send_button.config(bg="#000000", fg="#ffffff", activebackground="#4CAF50", activeforeground="#ffffff")
            self.online_list.config(bg="#2a2a2a", fg="#eeeeee")
            self.online_list_label.config(fg="#eeeeee")
        elif theme == "light":
            self.master.config(bg="#ffffff")
            self.chat_area.config(bg="#ffffff", fg="#000000", insertbackground="#000000", state=tk.DISABLED)
            self.message_entry.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
            self.send_button.config(bg="#4CAF50", fg="#ffffff", activebackground="#66BB6A", activeforeground="#ffffff")
            self.online_list.config(bg="#ffffff", fg="#000000")
            self.online_list_label.config(fg="#000000")
        self.current_theme = theme

    def _on_theme_change(self):
        selected_theme = self.theme_var.get()
        self._set_theme(selected_theme)
        self._save_config()

    def _load_config(self):
        """Načte konfiguraci klienta ze souboru config.json."""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.current_theme = config.get("theme", "light")
                    self.server_ip = config.get("server_ip")
                    self.server_port = config.get("server_port", SERVER_PORT) #načte port, pokud neni v configu, pouzije defaultni
                    if self.server_ip:
                         self.server_combobox.set("custom")
                         self.custom_ip_entry.insert(0, self.server_ip)
                         self.custom_port_entry.insert(0, str(self.server_port))
                    else:
                         self.server_combobox.set("cz.aetherus.mbservers.fun") #vychozi server
            except (json.JSONDecodeError, KeyError):
                print("Chyba při načítání konfigurace. Používám výchozí nastavení.")
                # Pokud dojde k chybě při čtení souboru, použijeme výchozí nastavení a soubor přepíšeme
                self._save_config()

    def _save_config(self):
        """Uloží aktuální konfiguraci (včetně motivu) do JSON souboru."""
        config = {
            "theme": self.current_theme,
            "server_ip": self.server_ip,
            "server_port": self.server_port,
        }
        try:
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f, indent=4)  # Používáme indent=4 pro hezčí formátování JSON
        except Exception as e:
            print(f"Chyba při ukládání konfigurace: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    client_gui = ChatClientGUI(root)
    root.mainloop()