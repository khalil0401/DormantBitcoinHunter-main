import requests
from bit import Key

# تحديد النطاق
start = int("000000000000000000000000000000000000000000000007f000000000000000", 16)
#start=70b2d798360074860
#end=7ffff000000000000
#70b2d798360074860:7ffff000000000000
end =   int("000000000000000000000000000000000000000000000007ffffffffffffffff", 16)

# وظيفة للتحقق من الرصيد
def check_BTC_balance(address):
        try:
            response = requests.get(f"https://blockchain.info/balance?active={address}", timeout=10)
            response.raise_for_status()
            data = response.json()
            print(data)
            balance = data[address]["final_balance"]
            return balance / 100000000
        except requests.RequestException as e:
                logging.error("Error checking balance: %s", str(e))
        return -1

current = start
print(f"current: {current} \n   end: {end} ")
while current <= end:    
    private_key_hex = hex(current)[2:] 
    current += 1 

   
    try:
        key = Key.from_hex(private_key_hex)
        address = key.address

    except Exception as e:
        print(f"Error generating key: {e}")
        continue

    if address+""=="1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9":
        with open("found_keys.txt", "a") as file:
            file.write(f"Private Key: {private_key_hex}, Address: {address} \n")
        print(f"Found! Private Key: {private_key_hex}, Address: {address}")
        exit()
    else:
        print(f"Checked Address: {address}, Private Key: {private_key_hex}")
