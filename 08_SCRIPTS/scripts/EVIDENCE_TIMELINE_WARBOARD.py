
import tkinter as tk

def launch_timeline_warboard():
    window = tk.Tk()
    window.title("Evidence Timeline Warboard")
    label = tk.Label(window, text="Timeline Warboard Active", font=("Arial", 16))
    label.pack(pady=20)
    window.mainloop()

if __name__ == "__main__":
    launch_timeline_warboard()
