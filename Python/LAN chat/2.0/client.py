import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, Menu, Canvas
import socket
import threading
import io
from PIL import Image, ImageDraw, ImageTk
#import cairosvg  # Importujeme knihovnu cairosvg

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345


class ChatClientGUI:
    def __init__(self, master):
        self.master = master
        master.title("Aetherus Chat")
        #master.iconbitmap("aetherus.ico")  # Odstraníme nastavení ikony z ICO souboru
        self.nickname = None
        self.client_socket = None
        self.debug_enabled = tk.BooleanVar()
        self.debug_enabled.set(False)

        self._create_menu()
        self._create_widgets()
        self._load_icon()

        master.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _create_menu(self):
        menubar = Menu(self.master)
        debugmenu = Menu(menubar, tearoff=0)
        debugmenu.add_checkbutton(label="Debug", variable=self.debug_enabled)
        menubar.add_cascade(label="Nastavení", menu=debugmenu)
        self.master.config(menu=menubar)

    def _debug_print(self, message):
        if self.debug_enabled.get():
            print(f"(DEBUG): {message}")

    def _create_widgets(self):
        self.connect_frame = tk.Frame(self.master)
        self.connect_frame.pack(pady=10)

        self.ip_label = tk.Label(self.connect_frame, text="IP Adresa Serveru:")
        self.ip_label.pack(side=tk.LEFT)

        self.ip_entry = tk.Entry(self.connect_frame)
        self.ip_entry.insert(0, SERVER_HOST)
        self.ip_entry.pack(side=tk.LEFT)

        self.port_label = tk.Label(self.connect_frame, text="Port:")
        self.port_label.pack(side=tk.LEFT, padx=5)

        self.port_entry = tk.Entry(self.connect_frame, width=5)
        self.port_entry.insert(0, str(SERVER_PORT))
        self.port_entry.pack(side=tk.LEFT)

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

        self.icon_canvas = Canvas(self.master, width=100, height=100)
        self.icon_canvas.pack(padx=10, pady=10, anchor=tk.NW)

    def _load_icon(self):
        """Načte a zobrazí SVG ikonu."""
        # Použijeme knihovnu cairosvg k převodu SVG na PNG data.
        # Pro správnou funkci je třeba mít nainstalované cairosvg a jeho závislosti (cairo, libxml2, atd.).
        try:
            import cairosvg
            # Načteme SVG data ze souboru.
            with open("icon.svg", "rb") as f:
                svg_data = f.read()
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=100, output_height=100)
            # Převedeme PNG data na PIL Image
            img = Image.open(io.BytesIO(png_data))
            self.icon_image = ImageTk.PhotoImage(img)
            self.icon_canvas.create_image(0, 0, anchor=tk.NW, image=self.icon_image)

            # Hack pro nastavení ikony okna.  Toto funguje jen na některých systémech a správce oken.
            # Je to spíše demonstrace možnosti, než robustní řešení.
            def set_window_icon(root, icon_data):
                import base64
                import subprocess
                if root.tk.call('tk', 'windowingsystem') == 'win32':
                    # Windows
                    ICON_DATA = base64.b64encode(icon_data).decode('ascii')
                    script = f'''
import base64, sys, ctypes
from ctypes import wintypes
ICON_DATA = b"{ICON_DATA}"
temp = open("icon.ico", "wb")
temp.write(base64.b64decode(ICON_DATA))
temp.close()
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
h = ctypes.windll.user32.LoadImageW(0, "icon.ico", 1, 0, 0, 0x00000010)
if h:
    ctypes.windll.user32.SendMessageW(root.winfo_id(), 0x0080, 0, h)
    sys.exit()
'''
                    # create a temporary file
                    with open('icon.py', 'w') as f:
                        f.write(script)
                    subprocess.Popen(['python', 'icon.py'], creationflags=subprocess.CREATE_NO_WINDOW)
                    #os.remove("icon.ico") # Remove temp icon
                else:
                    print("Setting window icon from PNG data is not supported on this platform.")

            set_window_icon(self.master, png_data) # Nastavíme ikonu okna z PNG dat

        except ImportError:
            print("Knihovna cairosvg není nainstalována.  Ikonu okna nelze zobrazit.")
            # Zde by bylo vhodné zobrazit uživateli upozornění, že se ikona nezobrazí.
            # messagebo

    def _connect_to_server(self):
        server_ip = self.ip_entry.get()
        server_port = int(self.port_entry.get())
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((server_ip, server_port))
            self._display_message(f"Připojeno k serveru na {server_ip}:{server_port}\n")
            self.connect_button.config(state=tk.DISABLED)

            nickname = simpledialog.askstring("Nickname", "Zadejte svůj nickname:", parent=self.master)
            if nickname:
                self.nickname = nickname
                self.client_socket.send(self.nickname.encode('utf-8'))
                threading.Thread(target=self._receive_messages, daemon=True).start()
            else:
                self._disconnect()
        except ConnectionRefusedError:
            messagebox.showerror("Chyba", f"Nelze se připojit k serveru na {server_ip}:{server_port}. Ujistěte se, že server běží.")
        except socket.error as e:
            messagebox.showerror("Chyba", f"Chyba připojení: {e}")

    def _receive_messages(self):
        while self.client_socket:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("§"):
                    self._update_online_users(message)
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
            self._display_message("Odpojeno od serveru.")
            self.connect_button.config(state=tk.NORMAL)

    def _on_closing(self):
        if messagebox.askokcancel("Ukončit", "Opravdu chcete ukončit chat?"):
            self._disconnect()
            self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    client_gui = ChatClientGUI(root)
    root.mainloop()

