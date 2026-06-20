import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json

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

# UI Layout
root = tk.Tk()
root.title("Stealth Tasker - Weekly Schedule Planner")
root.geometry("1350x750")
root.configure(bg="#f0f0f0")

# Save/Load Buttons
file_frame = tk.Frame(root, bg="#f0f0f0")
file_frame.pack(pady=5)
tk.Button(file_frame, text="Save All Tasks", command=save_tasks).pack(side="left", padx=10)
tk.Button(file_frame, text="Load Tasks", command=load_tasks).pack(side="left", padx=10)

# Input Form
input_frame = tk.LabelFrame(root, text="Add New Task", padx=10, pady=10, font=("Arial", 11, "bold"))
input_frame.pack(pady=10)

input_inner_frame = tk.Frame(input_frame)
input_inner_frame.pack()

# Labels
tk.Label(input_inner_frame, text="Task", font=("Arial", 9)).grid(row=0, column=0, padx=5)
tk.Label(input_inner_frame, text="Start Time", font=("Arial", 9)).grid(row=0, column=1, padx=5)
tk.Label(input_inner_frame, text="End Time", font=("Arial", 9)).grid(row=0, column=2, padx=5)
tk.Label(input_inner_frame, text="Day", font=("Arial", 9)).grid(row=0, column=3, padx=5)
tk.Label(input_inner_frame, text="Color", font=("Arial", 9)).grid(row=0, column=4, padx=5)

# Inputs
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