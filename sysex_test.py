import mido
import time

class XPS30Engine:
    def __init__(self):
        # 1. The Global Header for XPS-30
        self.header = [0x41, 0x10, 0x00, 0x00, 0x3A, 0x12]
        
        # 2. The Memory Map Dictionary
        # This is where we will translate the PDF manual into Python.
        # Format: "human_readable_name": [Byte1, Byte2, Byte3, Byte4]
        self.address_map = {
            "chorus_type": [0x10, 0x00, 0x04, 0x00],
            "chorus_level": [0x10, 0x00, 0x04, 0x01],
            "reverb_type": [0x10, 0x00, 0x04, 0x14],
            # We will add hundreds of parameters here eventually!
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
        
        # Some Roland commands need multiple data bytes, so we handle lists or single numbers
        data = [value] if isinstance(value, int) else value
            
        payload = address + data
        checksum = self.calculate_checksum(payload)
        
        return mido.Message('sysex', data=self.header + payload + [checksum])

# ==========================================
# TEST SCRIPT
# ==========================================
def test_engine():
    # Initialize our new brain
    synth = XPS30Engine()
    
    ports = mido.get_output_names()
    target_port = next((p for p in ports if 'JUNO-DS 1' in p or 'XPS-30' in p), None)
            
    if not target_port:
        print("Error: Keyboard not found.")
        return

    print(f"Engine Connected to: {target_port}")
    
    with mido.open_output(target_port) as outport:
        print("\nTesting the Dynamic Engine...")
        
        # Test 1: Set Chorus Type to DELAY (02)
        print("1. Setting Chorus to DELAY...")
        msg1 = synth.get_message("chorus_type", 2)
        outport.send(msg1)
        time.sleep(1)

        # Test 2: Set Chorus Type back to OFF (00)
        print("2. Setting Chorus to OFF...")
        msg2 = synth.get_message("chorus_type", 0)
        outport.send(msg2)
        time.sleep(1)

        print("\nSuccess! The Engine is dynamically generating SysEx.")

if __name__ == "__main__":
    test_engine()