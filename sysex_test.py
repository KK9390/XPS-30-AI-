import mido
import time
import argparse

class XPS30Engine:
    def __init__(self):
        self.header = [0x41, 0x10, 0x00, 0x00, 0x3A, 0x12]
        
        self.address_map = {
            "patch_cutoff": [0x1F, 0x00, 0x00, 0x22],
            "patch_reverb": [0x1F, 0x00, 0x04, 0x01],
            "perf_cutoff":  [0x10, 0x00, 0x20, 0x11],
            "perf_reverb":  [0x10, 0x00, 0x20, 0x1E]
        }
        
        # --- THE HARDWARE COMPLIANCE RULES ---
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
        
        # 1. Compliance Check: Clamp the value to the exact XPS-30 limits
        clamped_value = max(rule["min"], min(rule["max"], user_value))
        
        # 2. Hardware Translation: Convert negative screen values to SysEx payload bytes
        sysex_byte = clamped_value + rule["shift"]
            
        payload = self.address_map[param_name] + [sysex_byte]
        checksum = self.calculate_checksum(payload)
        
        return mido.Message('sysex', data=self.header + payload + [checksum])

# ==========================================
# 🤖 AI COMMAND TRANSMITTER (SYSEX EXACT)
# ==========================================
def apply_ai_parameters(cutoff, effect):
    synth = XPS30Engine()
    
    ports = mido.get_output_names()
    target_port = next((p for p in ports if 'JUNO-DS 1' in p or 'XPS-30' in p), None)
            
    if not target_port:
        print("Error: Keyboard not found.")
        return

    with mido.open_output(target_port) as outport:
        print(f"\n🤖 Link Established to: {target_port}")
        print(f"📡 Transmitting AI Analysis Data via SysEx Memory Overwrite...")
        
        if cutoff is not None:
            print(f"   -> Setting Filter Cutoff memory to: {cutoff}")
            # Blast to both modes so it works no matter what screen you are on
            outport.send(synth.get_message("patch_cutoff", cutoff))
            time.sleep(0.05)
            outport.send(synth.get_message("perf_cutoff", cutoff))
            time.sleep(0.05)
            
        if effect is not None:
            print(f"   -> Setting Effect Level memory to: {effect}")
            outport.send(synth.get_message("patch_reverb", effect))
            time.sleep(0.05)
            outport.send(synth.get_message("perf_reverb", effect))
            time.sleep(0.05)
            
        print("✅ Success! Parameters written to Temporary Memory. The * should now be visible.")

# ==========================================
# THE ARGUMENT CATCHER
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roland AI Bridge")
    parser.add_argument('--cutoff', type=int, help='Filter Cutoff (0-127)')
    parser.add_argument('--effect', type=int, help='Effect Level (0-127)')
    args = parser.parse_args()

    if args.cutoff is not None or args.effect is not None:
        apply_ai_parameters(args.cutoff, args.effect)
    else:
        print("Run with --cutoff and --effect arguments from the command line!")
