import os
from bit import Key
from bit.format import bytes_to_wif
import random
from rich.console import Console
import addresses

# إعداد الكونسول
console = Console()
addresses_set = set(addresses.addresses)
console.clear()

# عرض رسالة بدء البرنامج
console.print(" [yellow]-----------------KEYS.LOL----------------------[/yellow]")
console.print("[yellow]                 Starting search...[/yellow]")
console.print("[yellow]                Using Blockchain API...[/yellow]")
console.print(" [yellow]-----------------KEYS.LOL----------------------[/yellow]")

# تحديد النطاق بالأرقام
start_range = int("0000000000000000000000000000000000000000000000040000000000000000", 16)
stop_range =  int("000000000000000000000000000000000000000000000007ffffffffffffffff", 16)

console.print("[purple]⏳ Starting search... Please Wait ⏳[/purple]")
console.print("==========================================================")

# دالة لتوليد المفاتيح والعناوين
def generate_keys_and_addresses(base_key, num_keys=128):
    keys = [Key.from_int(base_key + i) for i in range(num_keys)]
    addresses = [
        (
            key.to_hex(), 
            key.address,  # العنوان المضغوط
            Key(bytes_to_wif(key.to_bytes(), compressed=False)).address,  # العنوان غير المضغوط
            bytes_to_wif(key.to_bytes(), compressed=False),  # المفتاح (غير مضغوط)
            bytes_to_wif(key.to_bytes(), compressed=True)  # المفتاح (مضغوط)
        )
        for key in keys
    ]
    return addresses

# دالة للتحقق من وجود تطابق
def check_addresses(addresses, page_number):
    for keyHex, address, addressu, wifu, wifc in addresses:
        if address in addresses_set or addressu in addresses_set:
            console.print(f'[bold green]📋 Page Number : [{page_number}] [/bold green]')
            console.print('💸💰🤩 Matching Key Found! 💸💰🤩')
            console.print(f"Key Hex: {keyHex}")
            console.print(f"Compressed Address: {address}")
            console.print(f"Uncompressed Address: {addressu}")
            console.print(f"Private Key (WIF, Compressed): {wifc}")
            console.print(f"Private Key (WIF, Uncompressed): {wifu}")
            save_winner(page_number,keyHex, address, addressu, wifu, wifc)
            return True
        print(keyHex)    
    return False

# دالة لحفظ النتائج
def save_winner(page_number, keyHex,address, addressu, wifu, wifc):
    with open("winner.txt", "a") as f:
        f.write('\n============= Bitcoin Address with Balance Found =============\n')
        f.write(f'Key Hex: {keyHex}\n')
        f.write(f'Page Number: {page_number}\n')
        f.write(f'Compressed Address: {address}\n')
        f.write(f'Uncompressed Address: {addressu}\n')
        f.write(f'Private Key (WIF, Uncompressed): {wifu}\n')
        f.write(f'Private Key (WIF, Compressed): {wifc}\n')
        f.write('==========================================================\n')

# بدء عملية الفحص
counter = 0
max_attempts = 1000  # الحد الأقصى لعدد المحاولات
num_keys=1024
try:
    while True:
        base_key = random.randint(start_range, stop_range - num_keys)
        page_number = (base_key - start_range) // num_keys + 1
        addresses = generate_keys_and_addresses(base_key,num_keys)

        if check_addresses(addresses, page_number):
            break  # إنهاء الحلقة إذا تم العثور على تطابق

        counter += 1
        #console.print(f"[red]📋 Page Number : [{page_number}] | Total Scanned: {counter * 128} [/red]")

    else:
        console.print("[yellow]⚠️ Maximum attempts reached. Exiting... ⚠️[/yellow]")

except KeyboardInterrupt:
    console.print("[red]⛔️ Scan interrupted by user. Exiting... ⛔️[/red]")
