import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, Entry, Button, END, Label
import os  # Import modulu os
from PIL import Image, ImageTk  # Import Pillow

def get_local_ip():
    """
    Získá lokální IP adresu počítače.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "127.0.0.1"

def broadcast(message, clients, text_area):
    """
    Odešle zprávu všem klientům a zobrazí ji v textovém poli.
    """
    for client in clients:
        try:
            client.send(message)
        except:
            remove(client, clients, text_area)  # Pass text_area to remove
    text_area.insert(END, message.decode('utf-8') + '\n')
    text_area.see(END)

def handle_client(client, clients, nicknames, text_area):
    """
    Obsluha komunikace s jedním klientem.
    """
    while True:
        try:
            message = client.recv(1024)
            broadcast(message, clients, text_area)
        except:
            index = clients.index(client)
            nickname = nicknames[index]
            broadcast(f'{nickname} se odpojil.'.encode('utf-8'), clients, text_area)
            remove(client, clients, text_area)  # Pass text_area to remove
            break

def remove(client, clients, text_area):
    """
    Odstraní klienta ze seznamu a zobrazí zprávu v textovém poli.
    """
    if client in clients:
        index = clients.index(client)
        clients.remove(client)
        if index < len(nicknames):
            nicknames.pop(index)
        text_area.insert(END, f'Klient {client.getpeername()} se odpojil.\n') #show disconnected client
        text_area.see(END)



if __name__ == "__main__":
    root = tk.Tk()
    root.title("LAN Chat")

    # Načtení obrázku pozadí
    bg_image_global = None
    try:
        # Zkontroluje, zda soubor existuje a je to soubor
        if os.path.exists("background.jpeg") and os.path.isfile("background.jpeg"):
            img = Image.open("background.jpeg")  # Otevře obrázek pomocí Pillow

            # Získání rozměrů obrázku
            img_width, img_height = img.size

            # Zvětšení rozměrů 1.5x
            new_width = int(img_width * 1.5)
            new_height = int(img_height * 1.5)
            img = img.resize((new_width, new_height), Image.LANCZOS) # Použití kvalitnějšího algoritmu pro změnu velikosti

            # Nastavení velikosti okna na nové rozměry obrázku
            root.geometry(f"{new_width}x{new_height}")
            bg_image = ImageTk.PhotoImage(img)  # Převede obrázek pro Tkinter
            bg_image_global = bg_image
            bg_label = tk.Label(root, image=bg_image)
            bg_label.image = bg_image  # keep a reference!
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)  # Umístí obrázek na celou plochu okna
        else:
            print("Obrázek pozadí nebyl nalezen nebo není soubor. Použije se výchozí pozadí.")
            root.geometry("800x800")  # Nastavení výchozí velikosti okna
    except Exception as e:
        print(f"Nepodařilo se načíst obrázek pozadí: {e}. Použije se výchozí pozadí.")
        root.geometry("800x800")  # Nastavení výchozí velikosti okna

    root.resizable(False, False)  # Okno nepůjde zvětšovat ani zmenšovat

    # Proměnné pro ukládání vstupů
    entry_ip_server = None
    entry_port_server = None
    text_area_server = None
    entry_message_server = None #server
    button_send_server = None #server

    entry_ip_client = None
    entry_port_client = None
    entry_nickname = None
    text_area_client = None
    entry_message_client = None  #client
    button_send_client = None #client

    # Declare clients and nicknames as global variables
    clients = []
    nicknames = []
    
    def send_message_server():
        """
        Odešle zprávu ze serveru všem klientům.
        """
        global clients, text_area_server  # Ensure access to the global variables
        message = f'Server: {entry_message_server.get()}'.encode('utf-8')
        broadcast(message, clients, text_area_server)
        entry_message_server.delete(0, END)

    def server_program(root, bg_image_global):
        """
        Funkce serveru s GUI.
        """
        global entry_ip_server, entry_port_server, text_area_server, entry_message_server, button_send_server, clients, nicknames
        # Získání vstupů z GUI
        host = entry_ip_server.get()
        if not host:
            host = get_local_ip()
        port = int(entry_port_server.get())
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server.bind((host, port))
        except socket.error as e:
            text_area_server.insert(END, f"Chyba při spouštění serveru: {e}\n")
            text_area_server.see(END)
            return
        server.listen()

        # Initialize clients and nicknames lists
        clients = []
        nicknames = []

        text_area_server.insert(END, f'Server naslouchá na {host}:{port}\n')
        text_area_server.see(END)

        def accept_clients():
            while True:
                client, address = server.accept()
                text_area_server.insert(END, f'Připojil se klient: {address}\n')
                text_area_server.see(END)

                client.send('NICK'.encode('utf-8'))
                nickname = client.recv(1024).decode('utf-8').strip()
                nicknames.append(nickname)
                clients.append(client)

                text_area_server.insert(END, f'Nickname klienta je: {nickname}\n')
                text_area_server.see(END)
                broadcast(f'{nickname} se připojil.'.encode('utf-8'), clients, text_area_server)

                thread = threading.Thread(target=handle_client, args=(client, clients, nicknames, text_area_server))
                thread.start()

        # Spusť přijímání klientů v samostatném vlákně, aby GUI nezamrzlo
        threading.Thread(target=accept_clients).start()

        # GUI pro server
        label_server = Label(root, text="Server", font=("Arial", 16))  # Nadpis Server
        label_server.pack()
        text_area_server = scrolledtext.ScrolledText(root, width=60, height=20)
        text_area_server.pack()

        label_ip_server = Label(root, text="IP adresa serveru:")
        label_ip_server.pack()
        entry_ip_server = Entry(root, width=50)
        entry_ip_server.pack()
        entry_ip_server.insert(0, get_local_ip())

        label_port_server = Label(root, text="Port serveru:")
        label_port_server.pack()
        entry_port_server = Entry(root, width=50)
        entry_port_server.pack()
        entry_port_server.insert(0, "12345")

        button_start_server = Button(root, text="Spustit server", command=lambda: server_program(root, bg_image_global))
        button_start_server.pack()
        
        # These lines were moved from server_program to here
        label_message_server = Label(root, text="Zpráva serveru:")
        label_message_server.pack()
        entry_message_server = Entry(root, width=50)
        entry_message_server.pack()
        button_send_server = Button(root, text="Odeslat zprávu jako server", command=send_message_server)
        button_send_server.pack()

        if bg_image_global:
            bg_label = tk.Label(root, image=bg_image_global)
            bg_label.image = bg_image_global
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def client_program(root, bg_image_global):
        """
        Funkce klienta s GUI.
        """
        global entry_ip_client, entry_port_client, entry_nickname, text_area_client, entry_message_client, button_send_client
        # Získání vstupů z GUI
        server_ip = entry_ip_client.get()
        port = int(entry_port_client.get())
        nickname = entry_nickname.get()

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((server_ip, port))
        except socket.error as e:
            text_area_client.insert(END, f"Chyba připojení k serveru: {e}\n")
            text_area_client.see(END)
            return

        def receive():
            """
            Funkce pro příjem zpráv od serveru.
            """
            while True:
                try:
                    message = client.recv(1024).decode('utf-8')
                    if message == 'NICK':
                        client.send(nickname.encode('utf-8'))
                    else:
                        text_area_client.insert(END, message + '\n')
                        text_area_client.see(END)
                except:
                    text_area_client.insert(END, "Odpojeno od serveru.\n")
                    text_area_client.see(END)
                    client.close()
                    break

        def write():
            """
            Funkce pro odesílání zpráv na server.
            """
            message = f'{nickname}: {entry_message_client.get()}'.encode('utf-8')
            client.send(message)
            entry_message_client.delete(0, END)

        receive_thread = threading.Thread(target=receive)
        receive_thread.start()

        # GUI pro klienta
        label_client = Label(root, text="Klient", font=("Arial", 16))  # Nadpis Klient
        label_client.pack()
        text_area_client = scrolledtext.ScrolledText(root, width=60, height=20)
        text_area_client.pack()

        label_ip_client = Label(root, text="IP adresa serveru:")
        label_ip_client.pack()
        entry_ip_client = Entry(root, width=50)
        entry_ip_client.pack()
        entry_ip_client.insert(0, get_local_ip())


        label_port_client = Label(root, text="Port serveru:")
        label_port_client.pack()
        entry_port_client = Entry(root, width=50)
        entry_port_client.pack()
        entry_port_client.insert(0, "12345")

        label_nickname = Label(root, text="Tvůj nickname:")
        label_nickname.pack()
        entry_nickname = Entry(root, width=50)
        entry_nickname.pack()

        # Přidání odesílacího pole a tlačítka pro klienta
        label_message_client = Label(root, text="Tvoje zpráva:")  # Popisek pro vstupní pole
        entry_message_client = Entry(root, width=50)
        entry_message_client.pack()
        button_send_client = Button(root, text="Odeslat zprávu", command=write)
        button_send_client.pack()

        button_connect_client = Button(root, text="Připojit se", command=lambda: client_program(root, bg_image_global))
        button_connect_client.pack()
        
        if bg_image_global:
            bg_label = tk.Label(root, image=bg_image_global)
            bg_label.image = bg_image_global
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    def start_server_gui():
        global entry_ip_server, entry_port_server, text_area_server, entry_message_server, button_send_server
        # Zničit předchozí obsah okna
        for widget in root.winfo_children():
            widget.destroy()

        if bg_image_global:
            bg_label = tk.Label(root, image=bg_image_global)
            bg_label.image = bg_image_global
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # GUI pro server
        label_server = Label(root, text="Server", font=("Arial", 16))  # Nadpis Server
        label_server.pack()
        text_area_server = scrolledtext.ScrolledText(root, width=60, height=20)
        text_area_server.pack()

        label_ip_server = Label(root, text="IP adresa serveru:")
        label_ip_server.pack()
        entry_ip_server = Entry(root, width=50)
        entry_ip_server.pack()
        entry_ip_server.insert(0, get_local_ip())

        label_port_server = Label(root, text="Port serveru:")
        label_port_server.pack()
        entry_port_server = Entry(root, width=50)
        entry_port_server.pack()
        entry_port_server.insert(0, "12345")

        button_start_server = Button(root, text="Spustit server", command=lambda: server_program(root, bg_image_global))
        button_start_server.pack()
        
        # These lines were moved from server_program to here
        label_message_server = Label(root, text="Zpráva serveru:")
        label_message_server.pack()
        entry_message_server = Entry(root, width=50)
        entry_message_server.pack()
        button_send_server = Button(root, text="Odeslat zprávu jako server", command=send_message_server)
        button_send_server.pack()
        

    def start_client_gui():
        global entry_ip_client, entry_port_client, entry_nickname, text_area_client, entry_message_client, button_send_client
        # Zničit předchozí obsah okna
        for widget in root.winfo_children():
            widget.destroy()
        
        if bg_image_global:
            bg_label = tk.Label(root, image=bg_image_global)
            bg_label.image = bg_image_global
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # GUI pro klienta
        label_client = Label(root, text="Klient", font=("Arial", 16))  # Nadpis Klient
        label_client.pack()
        text_area_client = scrolledtext.ScrolledText(root, width=60, height=20)
        text_area_client.pack()

        label_ip_client = Label(root, text="IP adresa serveru:")
        label_ip_client.pack()
        entry_ip_client = Entry(root, width=50)
        entry_ip_client.pack()
        entry_ip_client.insert(0, get_local_ip())


        label_port_client = Label(root, text="Port serveru:")
        label_port_client.pack()
        entry_port_client = Entry(root, width=50)
        entry_port_client.pack()
        entry_port_client.insert(0, "12345")

        label_nickname = Label(root, text="Tvůj nickname:")
        label_nickname.pack()
        entry_nickname = Entry(root, width=50)
        entry_nickname.pack()

        # Přidání odesílacího pole a tlačítka pro klienta
        label_message_client = Label(root, text="Tvoje zpráva:")  # Popisek pro vstupní pole
        entry_message_client = Entry(root, width=50)
        entry_message_client.pack()
        button_send_client = Button(root, text="Odeslat zprávu", command=lambda: client_program(root, bg_image_global))
        button_send_client.pack()

        button_connect_client = Button(root, text="Připojit se", command=lambda: client_program(root, bg_image_global))
        button_connect_client.pack()
        

    # Úvodní obrazovka s tlačítky pro výběr serveru nebo klienta
    label_welcome = Label(root, text="Vítejte v LAN Chatu!", font=("Arial", 20))  # Úvodní nadpis
    label_welcome.pack(pady=10)  # Přidá mezery kolem nadpisu
    button_server_select = Button(root, text="Spustit server", command=start_server_gui)
    button_server_select.pack(pady=5)  # Přidá mezery kolem tlačítek
    button_client_select = Button(root, text="Připojit se ke klientovi", command=start_client_gui)
    button_client_select.pack(pady=5)

    root.mainloop()

