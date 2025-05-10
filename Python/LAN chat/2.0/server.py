import socket
import threading

HOST = '0.0.0.0'  # Naslouchá na všech dostupných rozhraních
PORT = 12345
clients = {}  # Slovník pro ukládání klientů (IP: (nickname, socket))
DEBUG = True  # Debugování je na serveru vždy zapnuté

def debug_print(message):
    if DEBUG:
        print(message)

def broadcast(message, sender_socket):
    for ip, (nick, client) in clients.items():
        if client != sender_socket:
            try:
                client.send(message)
            except:
                # Pokud se nepodaří odeslat (odpojený klient), můžeme ho odstranit
                pass

def send_private_message(sender_nick, recipient_nick, message):
    debug_print(f"Server: Pokus o odeslání soukromé zprávy od '{sender_nick}' pro '{recipient_nick}': '{message}'")
    recipient_socket = None
    for ip, (nick, sock) in clients.items():
        debug_print(f"Server: Kontroluji uživatele '{nick}' s IP '{ip}'")
        if nick == recipient_nick:
            recipient_socket = sock
            debug_print(f"Server: Našel příjemce '{nick}' - socket: {recipient_socket}")
            break

    if recipient_socket:
        try:
            recipient_socket.send(f"(Soukromá zpráva od {sender_nick}): {message}\n".encode('utf-8'))
            debug_print(f"Server: Soukromá zpráva odeslána na {recipient_nick}")
        except:
            debug_print(f"Server: Chyba při odesílání soukromé zprávy na {recipient_nick}")
            pass # Příjemce mohl být odpojen
    else:
        sender_socket = clients.get(get_ip_by_nickname(sender_nick), (None, None))[1]
        if sender_socket:
            sender_socket.send(f"Server: Uživatel '{recipient_nick}' není online.\n".encode('utf-8'))
            debug_print(f"Server: Uživatel '{recipient_nick}' není online")

def send_online_users():
    online_users = "§" + "\n".join(nick for ip, (nick, sock) in clients.items())
    debug_print(f"Server: Odesílám online uživatele (označené): '{online_users}'")
    for ip, (nick, client) in clients.items():
        try:
            client.send(online_users.encode('utf-8'))
        except:
            pass

def get_ip_by_nickname(nickname):
    for ip, (nick, sock) in clients.items():
        if nick == nickname:
            return ip
    return None

def handle_client(client_socket, client_address):
    global clients
    global broadcast
    global send_online_users
    global send_private_message

    ip_address = client_address[0]
    nickname = None

    try:
        # První připojení - získání nickname
        if ip_address not in clients:
            client_socket.send("NICK".encode('utf-8'))
            nickname = client_socket.recv(1024).decode('utf-8').strip()
            if nickname:
                clients[ip_address] = (nickname, client_socket)
                debug_print(f"Uživatel {nickname} ({ip_address}) se připojil.")
                broadcast(f"Server: Uživatel {nickname} se připojil.\n".encode('utf-8'), client_socket)
                send_online_users()
            else:
                debug_print(f"Připojení od {ip_address} ukončeno (chybný nickname).")
                client_socket.close()
                return
        else:
            # Klient se připojuje znovu - získá nový nickname
            client_socket.send("NICK".encode('utf-8'))
            new_nickname = client_socket.recv(1024).decode('utf-8').strip()
            if new_nickname:
                old_nickname, _ = clients[ip_address]
                clients[ip_address] = (new_nickname, client_socket)
                debug_print(f"Uživatel s IP {ip_address} změnil nickname z '{old_nickname}' na '{new_nickname}'.")
                broadcast(f"Server: Uživatel '{old_nickname}' se nyní jmenuje '{new_nickname}'.\n".encode('utf-8'), client_socket)
                send_online_users()
            else:
                debug_print(f"Připojení od {ip_address} ukončeno (chybný nový nickname).")
                client_socket.close()
                return

        # Komunikace s klientem
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                # Získání aktuálního nickname pro tuto IP adresu
                current_nickname = clients.get(ip_address, ('Neznámý',))[0]

                # Zpracování zprávy ve formátu "PRIJEMCE: ZPRAVA"
                if ":" in message:
                    recipient_nick, content = message.split(":", 1)
                    send_private_message(current_nickname, recipient_nick.strip(), content.strip())
                else:
                    debug_print(f"{current_nickname}: {message}")
                    broadcast(f"{current_nickname}: {message}\n".encode('utf-8'), client_socket)
            except ConnectionResetError:
                break
            except Exception as e:
                debug_print(f"Chyba při komunikaci s {clients.get(ip_address, ('Neznámý',))[0]} ({ip_address}): {e}")
                break

    finally:
        if ip_address in clients:
            disconnected_nickname = clients[ip_address][0]
            del clients[ip_address]
            debug_print(f"Uživatel {disconnected_nickname} ({ip_address}) se odpojil.")
            broadcast(f"Server: Uživatel {disconnected_nickname} se odpojil.\n".encode('utf-8'), None)
            send_online_users()
        client_socket.close()

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        print(f"Server naslouchá na {HOST}:{PORT}...")

        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Připojení od {client_address}")
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_thread.start()
    except socket.error as e:
        print(f"Chyba serveru: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()

if __name__ == "__main__":
    main()