import mido
import time
import argparse

class XPS30Engine:
    def __init__(self):
        # 1. The Global Header for XPS-30
        self.header = [0x41, 0x10, 0x00, 0x00, 0x3A, 0x12]
        
        # 2. The Memory Map Dictionary
        self.address_map = {
            "chorus_type": [0x10, 0x00, 0x04, 0x00],
            "chorus_level": [0x10, 0x00, 0x04, 0x01],
            "reverb_type": [0x10, 0x00, 0x04, 0x14],
            # --- NEW: AI Mapped Parameters ---
            "filter_cutoff": [0x18, 0x00, 0x20, 0x21], # Temporary Part 1 Cutoff
            "effect_level": [0x18, 0x00, 0x20, 0x25]   # Temporary Part 1 Reverb Send
        }

    def calculate_checksum(self, payload):
        """Roland's proprietary checksum math."""
        total_sum = sum(payload)
        remainder = total_sum % 128
        return 0 if (128 - remainder) == 128 else (128 - remainder)

    def get_message(self, param_name, value):
        """Builds the final MIDI message from English commands."""
        if param_name not in self.address_map:
            print(f"Error: I don't know the address for '{param_name}'")
            return None
            
        address = self.address_map[param_name]
        
        data = [value] if isinstance(value, int) else value
            
        payload = address + data
        checksum = self.calculate_checksum(payload)
        
        return mido.Message('sysex', data=self.header + payload + [checksum])

# ==========================================
# 🤖 AI COMMAND TRANSMITTER
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
        print(f"📡 Transmitting AI Analysis Data...")
        
        if cutoff is not None:
            print(f"   -> Setting Filter Cutoff to: {cutoff}")
            msg1 = synth.get_message("filter_cutoff", cutoff)
            outport.send(msg1)
            time.sleep(0.1) # Tiny pause so we don't choke the MIDI cable
            
        if effect is not None:
            print(f"   -> Setting Effect Level to: {effect}")
            msg2 = synth.get_message("effect_level", effect)
            outport.send(msg2)
            time.sleep(0.1)
            
        print("✅ Success! Parameters injected into Roland memory.")

# ==========================================
# ORIGINAL TEST SCRIPT
# ==========================================
def test_engine():
    synth = XPS30Engine()
    ports = mido.get_output_names()
    target_port = next((p for p in ports if 'JUNO-DS 1' in p or 'XPS-30' in p), None)
            
    if not target_port:
        print("Error: Keyboard not found.")
        return

    print(f"Engine Connected to: {target_port}")
    with mido.open_output(target_port) as outport:
        print("\nTesting the Dynamic Engine...")
        
        print("1. Setting Chorus to DELAY...")
        msg1 = synth.get_message("chorus_type", 2)
        outport.send(msg1)
        time.sleep(1)

        print("2. Setting Chorus to OFF...")
        msg2 = synth.get_message("chorus_type", 0)
        outport.send(msg2)
        time.sleep(1)
        print("\nSuccess! The Engine is dynamically generating SysEx.")

# ==========================================
# THE ARGUMENT CATCHER
# ==========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roland AI Bridge")
    parser.add_argument('--cutoff', type=int, help='Filter Cutoff (0-127)')
    parser.add_argument('--effect', type=int, help='Effect Level (0-127)')
    args = parser.parse_args()

    # If we type numbers in the command prompt, run the AI function!
    if args.cutoff is not None or args.effect is not None:
        apply_ai_parameters(args.cutoff, args.effect)
    # If we just double-click the .exe, run the original test!
    else:
        test_engine()
