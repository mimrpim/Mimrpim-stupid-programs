import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, Entry, Button, StringVar, Radiobutton, Label, messagebox, Menu
from PIL import Image, ImageTk
import os
import sys

# Globální proměnné
client_socket = None
client_nickname = ""
icon_filename = "icon.jpg"  # Výchozí hodnota
settings_file = "settings.txt"
root = None  # Globální proměnná pro hlavní okno Tkinter
clients = []  # List pro uložení socketů klientů na serveru
server_thread = None # Globální proměnná pro uložení vlákna serveru

def handle_client(connection, client_address, server_name, chat_box):
    """
    Spravuje komunikaci s jedním klientem.
    """
    try:
        client_nickname = connection.recv(1024).decode('utf-8')
        print(f"[+] Klient {client_nickname} se připojil.")
        root.after(0, lambda: update_chat_box(chat_box, f"[+] Klient {client_nickname} se připojil.\n"))
    except Exception as e:
        print(f"[Chyba při příjmu přezdívky od klienta: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při příjmu přezdívky od klienta: {e}]\n"))
        return

    try:
        connection.sendall(f"Vítejte na serveru {server_name}!".encode('utf-8'))
    except Exception as e:
        print(f"[Chyba při odesílání uvítací zprávy: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při odesílání uvítací zprávy: {e}]\n"))
        return

    try:
        while True:
            data = connection.recv(1024)
            if not data:
                break

            message = data.decode('utf-8')
            print(f"[{client_nickname}] {message}")
            root.after(0, lambda: update_chat_box(chat_box, f"[{client_nickname}] {message}\n"))

            for client in clients:
                try:
                    client.sendall(f"[{client_nickname}] {message}".encode('utf-8'))
                except Exception as e:
                    print(f"[Chyba při odesílání zprávy klientovi {client.getpeername()}: {e}]")
                    root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při odesílání zprávy klientovi {client.getpeername()}: {e}]\n"))
                    remove_client(client)

    except ConnectionResetError:
        print(f"[!] Klient {client_nickname} se odpojil.")
        root.after(0, lambda: update_chat_box(chat_box, f"[!] Klient {client_nickname} se odpojil.\n"))
    except Exception as e:
        print(f"[Chyba při komunikaci s klientem {client_address}: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při komunikaci s klientem {client_address}: {e}]\n"))
    finally:
        connection.close()
        remove_client(connection)
        print(f"[-] Spojení s {client_address} ukončeno.")
        root.after(0, lambda: update_chat_box(chat_box, f"[-] Spojení s {client_address} ukončeno.\n"))


def remove_client(client_socket):
    """
    Odstraní klienta ze seznamu připojených klientů.
    """
    if client_socket in clients:
        clients.remove(client_socket)



def start_server(host, port, server_name, chat_box):
    """
    Spustí server.
    """
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.bind((host, port))
    except Exception as e:
        print(f"[Chyba při spouštění serveru: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při spouštění serveru: {e}]\n"))
        messagebox.showerror("Chyba serveru", f"Nepodařilo se spustit server: {e}")
        return

    server.listen()
    print(f"[*] Server {server_name} spuštěn na {host}:{port}")
    root.after(0, lambda: update_chat_box(chat_box, f"[*] Server {server_name} spuštěn na {host}:{port}\n"))

    global clients
    clients = []

    try:
        while True:
            connection, client_address = server.accept()
            clients.append(connection)
            client_thread = threading.Thread(target=handle_client, args=(connection, client_address, server_name, chat_box))
            client_thread.start()
    except KeyboardInterrupt:
        print("[!] Ukončování serveru...")
        root.after(0, lambda: update_chat_box(chat_box, "[!] Ukončování serveru...\n"))
    except Exception as e:
        print(f"[Chyba serveru: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba serveru: {e}]\n"))
        messagebox.showerror("Chyba serveru", f"Chyba serveru: {e}")
    finally:
        for client in clients:
            client.close()
        server.close()
        print("[*] Server ukončen.")
        root.after(0, lambda: update_chat_box(chat_box, "[*] Server ukončen.\n"))



def start_client(host, port, nickname, chat_box, send_message_callback):
    """
    Spustí klienta a připojí se k serveru.
    """
    global client_socket  # Používáme globální proměnnou
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Inicializace zde
    try:
        client_socket.connect((host, port))
        print(f"[+] Připojen k serveru {host}:{port} jako {nickname}")
        root.after(0, lambda: update_chat_box(chat_box, f"[+] Připojen k serveru {host}:{port} jako {nickname}\n"))
    except Exception as e:
        print(f"[Chyba při připojování k serveru: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při připojování k serveru: {e}]\n"))
        messagebox.showerror("Chyba připojení", f"Nepodařilo se připojit k serveru: {e}")
        client_socket = None  # Nastavíme zpět na None v případě chyby
        return None

    try:
        welcome_message = client_socket.recv(1024).decode('utf-8')
        print(f"[+] {welcome_message}")
        root.after(0, lambda: update_chat_box(chat_box, f"[+] {welcome_message}\n"))
    except Exception as e:
        print(f"[Chyba při příjmu uvítací zprávy: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při příjmu uvítací zprávy: {e}]\n"))
        messagebox.showerror("Chyba připojení", "Nepodařilo se přijmout uvítací zprávu od serveru.")
        client_socket.close()
        client_socket = None
        return None

    try:
        client_socket.sendall(nickname.encode('utf-8'))
    except Exception as e:
        print(f"[Chyba při odesílání přezdívky: {e}]")
        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při odesílání přezdívky: {e}]\n"))
        messagebox.showerror("Chyba připojení", "Nepodařilo se odeslat přezdívku serveru.")
        client_socket.close()
        client_socket = None
        return None

    def receive_messages(client_socket, chat_box):
        """
        Přijímá zprávy ze serveru a vypisuje je.
        """
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    print("[!] Server se odpojil.")
                    root.after(0, lambda: update_chat_box(chat_box, "[!] Server se odpojil.\n"))
                    break
                message = data.decode('utf-8')
                print(message)
                root.after(0, lambda: update_chat_box(chat_box, message + "\n"))
        except ConnectionResetError:
            print("[!] Spojení se serverem bylo přerušeno.")
            root.after(0, lambda: update_chat_box(chat_box, "[!] Spojení se serverem bylo přerušeno.\n"))
        except Exception as e:
            print(f"[Chyba při příjmu zpráv ze serveru: {e}]")
            root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při příjmu zpráv ze serveru: {e}]\n"))
            messagebox.showerror("Chyba při příjmu", f"Chyba při příjmu zpráv ze serveru: {e}")
        finally:
            if client_socket:
                client_socket.close()
            print("[*] Vlákno pro příjem zpráv ukončeno.")
            root.after(0, lambda: update_chat_box(chat_box, "[*] Vlákno pro příjem zpráv ukončeno.\n"))
            # Zde by mohl být pokus o znovupřipojení

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket, chat_box))
    receive_thread.daemon = True
    receive_thread.start()
    return client_socket, nickname



def send_message(client_socket, message, nickname, chat_box):
    """
    Odesílá zprávy na server.
    """
    if client_socket:
        try:
            client_socket.sendall(message.encode('utf-8'))
        except Exception as e:
            print(f"[Chyba při odesílání zprávy na server: {e}]")
            root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při odesílání zprávy na server: {e}]\n"))
            messagebox.showerror("Chyba odesílání", f"Nepodařilo se odeslat zprávu: {e}")
    else:
        messagebox.showerror("Chyba odesílání", "Nejste připojen k serveru.")



def load_settings():
    """
    Načte nastavení aplikace ze souboru settings.txt.
    """
    global icon_filename
    try:
        if not os.path.exists(settings_file):
            with open(settings_file, "w") as f:
                f.write("icon=icon.jpg\n")
        with open(settings_file, "r") as f:
            for line in f:
                if line.startswith("icon="):
                    icon_filename = line.split("=")[1].strip()
                    break
    except Exception as e:
        print(f"[Chyba při načítání nastavení: {e}]")
        messagebox.showerror("Chyba nastavení", f"Nepodařilo se načíst nastavení aplikace: {e}. Používá se výchozí nastavení.")



def save_settings(icon_file):
    """
    Uloží nastavení aplikace do souboru settings.txt.
    """
    try:
        with open(settings_file, "w") as f:
            f.write(f"icon={icon_file}\n")
    except Exception as e:
        print(f"[Chyba při ukládání nastavení: {e}]")
        messagebox.showerror("Chyba nastavení", f"Nepodařilo se uložit nastavení aplikace: {e}.")



def create_gui(mode):
    """
    Vytvoří GUI pro chatovací aplikaci.
    """
    global root
    root = tk.Tk()
    root.title("ICQ 2.0")
    root.geometry("800x800")

    load_settings()
    global icon_filename

    # Nastavení ikony okna
    try:
        img = Image.open(icon_filename)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
    except Exception as e:
        print(f"Chyba při načítání ikony: {e}")
        messagebox.showerror("Chyba ikony",
                           f"Nepodařilo se načíst ikonu aplikace: {e}.\n"
                           f"Ujistěte se, že je soubor '{icon_filename}' ve stejném adresáři\n"
                           f"jako spouštěný skript, nebo vyberte jinou ikonu z menu Nastavení.")

    global client_socket
    global client_nickname

    chat_box = scrolledtext.ScrolledText(root, state=tk.DISABLED, height=10, width=50)
    chat_box.pack(pady=10, expand=True, fill=tk.BOTH)

    message_entry = Entry(root, width=50)
    message_entry.pack(pady=5, fill=tk.X)
    message_entry.config(state=tk.DISABLED)

    def send_message_handler():
        """Odešle zprávu a vyčistí vstupní pole."""
        message = message_entry.get()
        if message:
            if client_socket:
                send_message(client_socket, message, client_nickname, chat_box)
                root.after(0, lambda: update_chat_box(chat_box, f"[Já ({client_nickname}):] {message}\n"))
                message_entry.delete(0, tk.END)
            elif mode == "server":
                root.after(0, lambda: update_chat_box(chat_box, f"[Server]: {message}\n"))
                for client in clients:
                    try:
                        client.sendall(f"[Server]: {message}".encode('utf-8'))
                    except Exception as e:
                        print(f"[Chyba při odesílání zprávy klientovi: {e}]")
                        root.after(0, lambda: update_chat_box(chat_box, f"[Chyba při odesílání zprávy klientovi: {e}]\n"))
                        remove_client(client)
                message_entry.delete(0, tk.END)
            else:
                messagebox.showinfo("Nelze odeslat", "Nejste připojen k serveru.")

    send_button = Button(root, text="Odeslat", command=send_message_handler)
    send_button.pack(pady=5)
    send_button.config(state=tk.DISABLED)

    ip_port_frame = tk.Frame(root)
    ip_port_frame.pack(pady=10, fill=tk.X)
    ip_label = Label(ip_port_frame, text="IP adresa:")
    ip_label.pack(side=tk.LEFT)
    ip_entry = Entry(ip_port_frame, width=15)
    ip_entry.pack(side=tk.LEFT)
    port_label = Label(ip_port_frame, text="Port:")
    port_label.pack(side=tk.LEFT)
    port_entry = Entry(ip_port_frame, width=10)
    port_entry.pack(side=tk.LEFT)

    server_name_frame = tk.Frame(root)
    server_name_label = Label(server_name_frame, text="Název serveru:")
    server_name_label.pack(side=tk.LEFT)
    server_name_entry = Entry(server_name_frame)
    server_name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    nickname_frame = tk.Frame(root)
    nickname_label = Label(nickname_frame, text="Přezdívka:")
    nickname_label.pack(side=tk.LEFT)
    nickname_entry = Entry(nickname_frame, width=20)
    nickname_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)


    if mode == "server":
        server_name_frame.pack(fill=tk.X)
        nickname_frame.pack_forget()
        root.title("ICQ 2.0 - Server")
    elif mode == "klient":
        nickname_frame.pack(fill=tk.X)
        server_name_frame.pack_forget()
        root.title("ICQ 2.0 - Klient")

    def start_chat():
        """Spustí chatovací aplikaci."""
        global client_socket
        global client_nickname
        global icon_filename
        global server_thread # Používáme globální proměnnou
        host = ip_entry.get()
        port = int(port_entry.get())

        if mode == "server":
            server_name = server_name_entry.get()
            if not server_name:
                messagebox.showerror("Chybějící název", "Zadejte název serveru.")
                return

            # Spustíme server v samostatném vlákně
            server_thread = threading.Thread(target=start_server, args=(host, port, server_name, chat_box))
            server_thread.daemon = True  # Nastavíme vlákno jako démon
            server_thread.start()
            message_entry.config(state=tk.NORMAL)
            send_button.config(state=tk.NORMAL)
            start_button.config(state=tk.DISABLED) # Zablokujeme start tlačítko po spuštění

        elif mode == "klient":
            nickname = nickname_entry.get()
            if not nickname:
                messagebox.showerror("Chybějící přezdívka", "Zadejte svou přezdívku.")
                return

            client_socket, client_nickname = start_client(host, port, nickname, chat_box, send_message_handler)
            if client_socket:
                message_entry.config(state=tk.NORMAL)
                send_button.config(state=tk.NORMAL)
                start_button.config(state=tk.DISABLED)  # Zablokujeme start tlačítko po spuštění
            else:
                messagebox.showerror("Chyba", "Nepodařilo se připojit k serveru")

        # Načte vybranou ikonu a uloží nastavení
        load_settings()
        try:
            img = Image.open(icon_filename)
            photo = ImageTk.PhotoImage(img)
            root.iconphoto(True, photo)
        except Exception as e:
            print(f"Chyba při načítání ikony: {e}")
            messagebox.showerror("Chyba ikony",
                               f"Nepodařilo se načíst ikonu aplikace: {e}.\n"
                               f"Zkontrolujte, zda soubor existuje a je ve správném formátu, nebo vyberte jinou ikonu z menu Nastavení.")

    message_entry.bind("<Return>", lambda event: send_message_handler())

    start_button = Button(root, text="Spustit", command=start_chat)
    start_button.pack(pady=10)

    # Vytvoření menu
    menu_bar = Menu(root)
    root.config(menu=menu_bar)  # Přidání menu do okna

    # Vytvoření položky "Nastavení"
    settings_menu = Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Nastavení", menu=settings_menu)

    # Funkce pro změnu ikony a uložení nastavení
    def change_icon(icon_name):
        global icon_filename
        icon_filename = icon_name
        save_settings(icon_filename)
        try:
            img = Image.open(icon_filename)
            photo = ImageTk.PhotoImage(img)
            root.iconphoto(True, photo)
            messagebox.showinfo("Ikona změněna", f"Ikona aplikace byla změněna na {icon_filename}.")
        except Exception as e:
            print(f"Chyba při změně ikony: {e}")
            messagebox.showerror("Chyba ikony", f"Nepodařilo se změnit ikonu aplikace: {e}.\nZkontrolujte, zda soubor existuje a je ve správném formátu.")

    # Přidání položek pro výběr ikony do menu "Nastavení"
    settings_menu.add_command(label="icon.jpg", command=lambda: change_icon("icon.jpg"))
    settings_menu.add_command(label="icon_darkmode.jpg", command=lambda: change_icon("icon_darkmode.jpg"))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    root.rowconfigure(1, weight=0)
    root.rowconfigure(2, weight=0)

    root.mainloop()



def show_mode_selection():
    """
    Zobrazí úvodní obrazovku s výběrem režimu.
    """
    global root
    root = tk.Tk()
    root.title("ICQ 2.0 - Výběr režimu")
    root.geometry("300x200")

    load_settings()
    global icon_filename

    # Nastavení ikony okna
    try:
        img = Image.open(icon_filename)
        photo = ImageTk.PhotoImage(img)
        root.iconphoto(True, photo)
    except Exception as e:
        print(f"Chyba při načítání ikony: {e}")
        messagebox.showerror("Chyba ikony",
                           f"Nepodařilo se načíst ikonu aplikace: {e}.\n"
                           f"Ujistěte se, že je soubor '{icon_filename}' ve stejném adresáři\n"
                           f"jako spouštěný skript, nebo vyberte jinou ikonu z menu Nastavení.")

    def on_server_button_click():
        """Spustí režim serveru."""
        root.destroy()
        create_gui("server")

    def on_client_button_click():
        """Spustí režim klienta."""
        root.destroy()
        create_gui("klient")

    title_label = Label(root, text="Vyberte režim:", font=("Arial", 16))
    title_label.pack(pady=20)

    server_button = Button(root, text="Server", command=on_server_button_click, width=20, height=3)
    server_button.pack(pady=10)

    client_button = Button(root, text="Klient", command=on_client_button_click, width=20, height=3)
    client_button.pack(pady=10)

    root.mainloop()


def update_chat_box(chat_box, message):
    """
    Aktualizuje chat_box v hlavním vlákně Tkinteru.
    """
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, message)
    chat_box.config(state=tk.DISABLED)



if __name__ == "__main__":
    # Spustíme výběr režimu
    show_mode_selection()
