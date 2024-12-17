"""
Script discussed in the video:
    https://youtu.be/i2QaBjCvMN4

How to steal all bitcoin (on average 10^-60 of it per day)

This script checks whether a given Bitcoin private key (int) has
funds using a CSV snapshot of the blockchain ledger.
This ordered CSV of currently funded addresses can be downloaded from:
    http://addresses.loyce.club/
Individual addresses can be inspeacted at, e.g.:
    https://www.blockchain.com/btc/address/3N6dm7isxV1BhzGVazjEHapV7ApcvdxgLZ

Efficient python and C 99 algos to for the SECP256k1 log at:
    https://github.com/Telariust
See also the programs in
    https://privatekeys.pw/

Don't write me emails asking how to install python or something of the sort. 
If you ask me something, use an adult sentence structure and attire.
Disclaimer: Due to potential bugs, don't use functions from this script for anything of value!
"""
import requests
from binascii import unhexlify  # Used for secret to WIF
import gzip  # To load a CSV holding the current Bitcoin ledger
import time  # For logging, optional

from hashlib import sha256  # Used for secret to WIF
from bitcoinaddress import Wallet  # Used to turn WIF to ledger addresses, see last video
from ecdsa import SECP256k1  # Note: The library 'ecdsa' is also used by 'bitcoinaddress' library.


MIN_SECRET = 1
MAX_SECRET = int(SECP256k1.order) - 1
LOYCE_CLUB_LATEST_LEDGER_FILENAME = "blockchair_bitcoin_addresses_and_balance_LATEST.tsv.gz"


class Config:
    MIN_FUND = 1  # BTC
    MIN_FUND = int(input(" ✅ MIN_FUND BTC ✍️ -> "))
    TAKE_CHARS = 10  # Number of chars used as address fingerprint for shallow comparison.
    TAKE_CHARS = int(input(" ✅ Number of chars used as address fingerprint for shallow comparison ✍️ -> "))
    TIME_LOG_EPOCH = 1000
    LOYCE_CLUB_LATEST_LEDGER_BASEPATH = r"C:\\Users\\ATECH STORE\\Downloads\\"
    RANDOM_SEED = 0 # Use -1 to not use random private keys, otherwise 0 or any positive int.
    # Disclaimer: Again, don't actually use this script for anything of value and don't use a naive seed.

    if RANDOM_SEED >= 0:
        from random import Random
        random = Random()
        random.seed(RANDOM_SEED)


def _generate_secret(idx):
    """
    :param idx: Index from main loop (linear, monotonely growing). Starts at 1.
    :returns: private key, e.g. in base 10.
    """
    if Config.RANDOM_SEED >= 0:
        secret = Config.random.randint(MIN_SECRET, MAX_SECRET)
    else:
        # Some other custom function
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


def _fingerprint(word):
    """
    Identify by the last few characters (non-unique fingerprint)
    """
    assert len(word) >= Config.TAKE_CHARS
    word_end = word[-Config.TAKE_CHARS:]
    return word_end


def _funded_addresses_stream(log_lines=False):
    """
    Load list of addresses as stream.
    Note: This way we never need to hold all addresses at once.
    :param log_lines: Whether the loading process should be logged to stdout, in detail.
    """
    def from_ledger_line(raw_row):
        line = raw_row.decode('ascii').split('\t')
        address = line[0]
        fund_sting = line[1].strip('\n')
        fund = int(fund_sting) / 10**8
        return address, fund

    filepath = Config.LOYCE_CLUB_LATEST_LEDGER_BASEPATH + \
        LOYCE_CLUB_LATEST_LEDGER_FILENAME

    with gzip.open(filepath, 'r') as ledger_rows:
        for row_idx, raw_row in enumerate(ledger_rows):
            # Skip header of LOYCE_CLUB file, which has strings 'address', 'balance'
            if row_idx==0:
                continue

            funded_address, fund = from_ledger_line(raw_row)

            if fund < Config.MIN_FUND:
                if log_lines:
                    print(f"Ledger loaded with funds all down to {Config.MIN_FUND} BTC.\n")
                return

            if log_lines:
                print(f"row idx = {row_idx}\n\traw row = {raw_row}\n"
                    f"\taddress = {funded_address}\n\tfund    = {fund} BTC")

            yield funded_address


def _secret_to_wif(secret):
    #Compact version of code discussed in previous video, https://www.youtube.com/watch?v=LYN3h5DjeXw
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


if __name__ == "__main__":
    funded_addresses = _funded_addresses_stream(log_lines=True)
    funded_address_fingerprints = list(map(_fingerprint, funded_addresses))

    def is_fingerprint_match(address):
        """
        Compare end of address against all loaded (funded) address ends.
        """
        testing_fp = _fingerprint(address)
        for fp in funded_address_fingerprints:
            if testing_fp==fp:
                return True
        return False

    time_start = time.time()

    for idx in range(1, 10**30):

        # Log time
        if idx % Config.TIME_LOG_EPOCH == 0:
            runtime = round((time.time() - time_start) / 60, 3)
            print(f"\n\tidx = {idx}, runtime = {runtime} min\n")

        secret = _generate_secret(idx)

        wif = _secret_to_wif(secret)
        addresses = _wif_to_addresses(wif)  # addresses from generated secret

        if any(map(is_fingerprint_match, addresses)):
            # Rescan and log
            for funded_address in _funded_addresses_stream():
                this_funded_fp = _fingerprint(funded_address)
                for address in addresses:
                    # Reject matches of addresses of different types
                    if len(address) == len(funded_address) and \
                        _fingerprint(address) == this_funded_fp:

                        # Log. Note that you can check funded addresses at
                        #   https://www.blockchain.com/de/btc/address/<funded_address>
                        print(f"\nPartial match with {Config.TAKE_CHARS} characters for\n"
                                f"\t{secret} (testing secret)\n"
                                f"\t{wif} (testing wif)\n"
                                f"\t\t'{this_funded_fp}' (matching fingerprint)\n"
                                f"\t\t{address} (testing address)\n"
                                f"\t\t{funded_address} (existing funded address)\n")

                        if funded_address == address:
                            file1= open("found_keys.txt", "a")
                            file1.write(f"secret: {secret}, wif: {wif}, Address: {funded_address} \n")
                            file1.close()
                            exit("Perfect match!")
