from binascii import unhexlify
import gzip
import time
from hashlib import sha256
from bitcoinaddress import Wallet
from ecdsa import SECP256k1
from multiprocessing import Pool, cpu_count, Manager

MIN_SECRET = 100
MAX_SECRET = int(SECP256k1.order) - 1
LOYCE_CLUB_LATEST_LEDGER_FILENAME = "blockchair_bitcoin_addresses_and_balance_LATEST.tsv.gz"

class Config:
    MIN_FUND = 1  # BTC
    TIME_LOG_EPOCH = 1000
    MIN_FUND = 0.1
    LOYCE_CLUB_LATEST_LEDGER_BASEPATH = r"C:\\Users\\ATECH STORE\\Downloads\\"
    RANDOM_SEED = 0  # Use -1 to not use random private keys, otherwise 0 or any positive int.

    if RANDOM_SEED >= 0:
        from random import Random
        random = Random()
        random.seed(RANDOM_SEED)

def _generate_secret(idx):
    if Config.RANDOM_SEED >= 0:
        secret = Config.random.randint(MIN_SECRET, MAX_SECRET)
    else:
        secret = idx

    assert type(secret) == int and MIN_SECRET <= secret <= MAX_SECRET, secret
    return secret

def _wif_to_addresses(wif):
    wallet = Wallet(wif)
    mainnet = wallet.address.mainnet
    addresses = (
        mainnet.pubaddr1,
        mainnet.pubaddr1c,
        mainnet.pubaddr3,
        mainnet.pubaddrbc1_P2WPKH,
        mainnet.pubaddrbc1_P2WSH,
    )
    return addresses

def _funded_addresses_stream():
    def from_ledger_line(raw_row):
        line = raw_row.decode('ascii').split('\t')
        address = line[0]
        fund_string = line[1].strip('\n')
        fund = int(fund_string) / 10**8
        return address, fund

    filepath = Config.LOYCE_CLUB_LATEST_LEDGER_BASEPATH + LOYCE_CLUB_LATEST_LEDGER_FILENAME

    with gzip.open(filepath, 'r') as ledger_rows:
        for row_idx, raw_row in enumerate(ledger_rows):
            if row_idx == 0:
                continue
            funded_address, fund = from_ledger_line(raw_row)
            if fund < Config.MIN_FUND:
                return
            yield funded_address

def _secret_to_wif(secret):
    ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    hex_secret = "80" + hex(secret)[2:].zfill(64)
    hash_digest = sha256(unhexlify(sha256(unhexlify(hex_secret)).hexdigest())).hexdigest()
    check_sum = hash_digest[:8]
    def _get_char(idx):
        return ALPHABET[int(hex_secret + check_sum, 16) // (58**idx) % 58]
    chars = "".join(map(_get_char, range(100)))
    wif = chars[::-1].lstrip('1')
    return wif

def _secret_to_wif_works():
    WIF_OF_1_EXPECT = "5HpHagT65TZzG1PH3CSu63k8DbpvD8s5ip4nEB3kEsreAnchuDf"
    return _secret_to_wif(1) == WIF_OF_1_EXPECT

assert _secret_to_wif_works()

def process_key_range(start, end, funded_addresses, lock):
    time_start = time.time()
    for idx in range(start, end):
        if idx % Config.TIME_LOG_EPOCH == 0:
            runtime = round((time.time() - time_start) / 60, 3)
            print(f"\n\tidx = {idx}, runtime = {runtime} min\n")

        secret = _generate_secret(idx)
        wif = _secret_to_wif(secret)
        addresses = _wif_to_addresses(wif)
        
        for address in addresses:
            #print(
            #                    f"\t{secret} (testing secret)\n"
            #                    f"\t{wif} (testing wif)\n"
            #                    f"\t\t{address} (testing address)\n")

            if address in funded_addresses:
                with lock:
                    with open("found_keys.txt", "a") as file:
                        file.write(f"Secret: {secret}, WIF: {wif}, Address: {address}\n")
                print(f"\nMatch found! Secret: {secret}, WIF: {wif}, Address: {address}\n")
                return

if __name__ == "__main__":
    funded_addresses = set(_funded_addresses_stream())
    num_workers = cpu_count()
    key_range = 10**6
    ranges = [(i, i + key_range) for i in range(1, 10**9, key_range)]
    print(ranges)
    with Manager() as manager:
        lock = manager.Lock()
        with Pool(num_workers) as pool:
            pool.starmap(process_key_range, [(start, end, funded_addresses, lock) for start, end in ranges])
