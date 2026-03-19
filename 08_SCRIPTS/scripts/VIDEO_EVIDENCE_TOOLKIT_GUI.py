
import tkinter as tk
from tkinter import filedialog, messagebox
from FFMPEG_CHAIN import FFMPEGChain

ff = FFMPEGChain()

def select_file():
    return filedialog.askopenfilename(title="Select Video File")

def save_file(title, ext):
    return filedialog.asksaveasfilename(title=title, defaultextension=ext, filetypes=[("Video files", f"*{ext}"), ("All files", "*.*")])

def burn_timestamp_gui():
    input_path = select_file()
    output_path = save_file("Save Output With Timestamp", ".mp4")
    result = ff.burn_in_timestamp(input_path, output_path)
    messagebox.showinfo("Result", result.stderr or "Success")

def frame_hash_gui():
    input_path = select_file()
    output_path = save_file("Save Frame Hashes", ".md5")
    result = ff.generate_frame_hashes(input_path, output_path)
    messagebox.showinfo("Result", result.stderr or "Success")

def extract_metadata_gui():
    input_path = select_file()
    meta = ff.extract_metadata(input_path)
    messagebox.showinfo("Metadata Extracted", str(meta)[:1000] + "..." if isinstance(meta, dict) else meta)

def reencode_gui():
    input_path = select_file()
    output_path = save_file("Save Reencoded Video", ".mp4")
    result = ff.reencode_admissible(input_path, output_path)
    messagebox.showinfo("Result", result.stderr or "Success")

def waveform_gui():
    input_path = select_file()
    output_path = save_file("Save Waveform Image", ".png")
    result = ff.generate_waveform(input_path, output_path)
    messagebox.showinfo("Result", result.stderr or "Success")

def launch_video_toolkit_gui():
    root = tk.Tk()
    root.title("🎞️ Video Evidence Toolkit")
    root.geometry("400x300")
    tk.Button(root, text="🎥 Burn Timestamp", command=burn_timestamp_gui).pack(pady=8)
    tk.Button(root, text="🧬 Generate Frame Hashes", command=frame_hash_gui).pack(pady=8)
    tk.Button(root, text="📊 Extract Metadata", command=extract_metadata_gui).pack(pady=8)
    tk.Button(root, text="🔄 Reencode for Court", command=reencode_gui).pack(pady=8)
    tk.Button(root, text="🌊 Generate Waveform Image", command=waveform_gui).pack(pady=8)
    root.mainloop()

if __name__ == "__main__":
    launch_video_toolkit_gui()
