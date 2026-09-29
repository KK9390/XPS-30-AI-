import mido
import time
import tkinter as tk
from tkinter import ttk

class XPS30Engine:
    def __init__(self):
        self.header = [0x41, 0x10, 0x00, 0x00, 0x3A, 0x12]
        
        self.address_map = {
            "patch_cutoff": [0x1F, 0x00, 0x00, 0x22],
            "patch_reverb": [0x1F, 0x00, 0x04, 0x01],
            "perf_cutoff":  [0x10, 0x00, 0x20, 0x11],
            "perf_reverb":  [0x10, 0x00, 0x20, 0x1E]
        }
        
        # Hardware Compliance Rules
        self.rules = {
            "patch_cutoff": {"min": -63, "max": 63,  "shift": 64},
            "patch_reverb": {"min": 0,   "max": 127, "shift": 0},
            "perf_cutoff":  {"min": -64, "max": 63,  "shift": 64},
            "perf_reverb":  {"min": 0,   "max": 127, "shift": 0}
        }

    def calculate_checksum(self, payload):
        total_sum = sum(payload)
        remainder = total_sum % 128
        return 0 if (128 - remainder) == 128 else (128 - remainder)

    def get_message(self, param_name, user_value):
        if param_name not in self.address_map:
            return None
            
        rule = self.rules[param_name]
        clamped_value = max(rule["min"], min(rule["max"], user_value))
        sysex_byte = clamped_value + rule["shift"]
            
        payload = self.address_map[param_name] + [sysex_byte]
        checksum = self.calculate_checksum(payload)
        
        return mido.Message('sysex', data=self.header + payload + [checksum])

# ==========================================
# THE GUI APPLICATION
# ==========================================
class RolandApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Roland AI Bridge")
        self.root.geometry("400x500")
        self.root.configure(padx=20, pady=20)
        
        self.synth = XPS30Engine()

        # Title
        title = ttk.Label(root, text="Roland XPS-30 Tone Injector", font=("Segoe UI", 16, "bold"))
        title.pack(pady=(0, 20))

        # Cutoff Slider
        ttk.Label(root, text="Filter Cutoff Offset (-64 to +63)", font=("Segoe UI", 10)).pack()
        self.cutoff_var = tk.IntVar(value=0)
        self.cutoff_slider = ttk.Scale(root, from_=-64, to=63, variable=self.cutoff_var, command=self.update_labels)
        self.cutoff_slider.pack(fill='x', pady=5)
        self.cutoff_label = ttk.Label(root, text="0", font=("Segoe UI", 12, "bold"), foreground="#0078D7")
        self.cutoff_label.pack()

        # Effect Slider
        ttk.Label(root, text="Effect Level (0 to 127)", font=("Segoe UI", 10)).pack(pady=(15, 0))
        self.effect_var = tk.IntVar(value=0)
        self.effect_slider = ttk.Scale(root, from_=0, to=127, variable=self.effect_var, command=self.update_labels)
        self.effect_slider.pack(fill='x', pady=5)
        self.effect_label = ttk.Label(root, text="0", font=("Segoe UI", 12, "bold"), foreground="#0078D7")
        self.effect_label.pack()

        # Transmit Button
        self.btn = ttk.Button(root, text="📡 Transmit AI Data to Synth", command=self.transmit)
        self.btn.pack(pady=25, fill='x', ipady=5)

        # Digital Log Screen
        self.log_screen = tk.Text(root, height=8, bg="black", fg="#00FF00", font=("Consolas", 9), wrap="word")
        self.log_screen.pack(fill='both', expand=True)
        self.log("System Ready. Waiting for AI parameters...")

    def update_labels(self, event=None):
        self.cutoff_label.config(text=str(int(self.cutoff_var.get())))
        self.effect_label.config(text=str(int(self.effect_var.get())))

    def log(self, message):
        self.log_screen.insert(tk.END, message + "\n")
        self.log_screen.see(tk.END)
        self.root.update()

    def transmit(self):
        cutoff = int(self.cutoff_var.get())
        effect = int(self.effect_var.get())
        
        ports = mido.get_output_names()
        target_port = next((p for p in ports if 'JUNO-DS 1' in p or 'XPS-30' in p), None)
                
        if not target_port:
            self.log("\n❌ ERROR: XPS-30 not found. Check USB cable!")
            return

        with mido.open_output(target_port) as outport:
            self.log(f"\n🤖 Connected: {target_port}")
            self.log(f"-> Injecting Cutoff: {cutoff}")
            outport.send(self.synth.get_message("patch_cutoff", cutoff))
            time.sleep(0.05)
            outport.send(self.synth.get_message("perf_cutoff", cutoff))
            time.sleep(0.05)
            
            self.log(f"-> Injecting Effect: {effect}")
            outport.send(self.synth.get_message("patch_reverb", effect))
            time.sleep(0.05)
            outport.send(self.synth.get_message("perf_reverb", effect))
            
            self.log("✅ Success! Memory overwritten.")

if __name__ == "__main__":
    root = tk.Tk()
    
    # Make it look like a modern Windows app
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
        
    app = RolandApp(root)
    root.mainloop()
