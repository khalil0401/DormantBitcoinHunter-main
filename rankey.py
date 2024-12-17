import random
import os
import subprocess
import addresses

def run_addrgen_generate():
    """Generate a Bitcoin address using AddrGen."""
    result = subprocess.run(["AddrGen.exe"], capture_output=True, text=True)
    return result

def save_to_file(filename, data):
    """Safely save output to a file."""
    with open(filename, "a") as f:
        f.write(data + "\n")

# Set to store addresses
addresses_set = set(addresses.addresses)
i = 0

# Run the loop
while True:
    i += 1
    result = run_addrgen_generate()

    # Ensure AddrGen output exists
    if result.stdout:
        lines = result.stdout.split("\n")
        if len(lines) > 2 and lines[2] in addresses_set:
            print("-----------------winner-----------------------")
            print(result.stdout)
            
            save_to_file("winner.txt", result.stdout)

    # Print progress every 1000 iterations
    if i % 1000 == 0:
        print(f"[INFO] Processed {i} addresses")
