#!/usr/bin/env python3

# needed python libs
import os
import math
import time
import ecdsa
import sys
import smtplib
import hashlib
import base58
import binascii
import multiprocessing
import ssl
from email.message import EmailMessage
from bitcoinlib.keys import HDKey
from bitcoinlib.services.services import Service

# import our configs
import addresses
import env

# send email
def send_email(lucky_text):
        text = env.email_text + "\n" + lucky_text
        msg = EmailMessage()
        msg.set_content(text)
        msg['Subject'] = env.subject
        msg['From'] = env.SEND_FROM
        msg['To'] = env.SEND_TO
        context=ssl.create_default_context()
        s = smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT)
        s.starttls(context=context)
        s.login(env.USER, env.PASS)
        s.send_message(msg)
        s.quit()
        print('Lucky Email sent!')


# do your job !
def hunter(num_seconds, worker_idx, return_dict):

    # construct a set (inkl. hashtable) from the list of addresses for fast search
    addresses_set = set(addresses.addresses)

    i = 0
    start = time.time()
    while ((time.time() - start)) < num_seconds:
        private_key = os.urandom(32).hex()

        # Generate the public key using ecdsa (Elliptic Curve Digital Signature Algorithm)
        private_key_bytes = bytes.fromhex(private_key)
        sk = ecdsa.SigningKey.from_string(private_key_bytes, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        public_key = b'\x04' + vk.to_string()  # Prefix 0x04 for uncompressed keys

        # Compute the public key hash (RIPEMD-160(SHA-256(public_key)))
        sha256 = hashlib.sha256(public_key).digest()
        ripemd160 = hashlib.new('ripemd160', sha256).digest()

        # Add version byte (0x00 for Mainnet) to the public key hash
        versioned_hash = b'\x00' + ripemd160

        # Compute the checksum (first 4 bytes of SHA-256(SHA-256(versioned_hash)))
        checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]

        # Concatenate versioned hash and checksum
        binary_address = versioned_hash + checksum

        # Convert to Base58
        address = base58.b58encode(binary_address).decode('utf-8')
        # override address for testing email-sending 
        #if worker_idx == 0 and i == 0:
        #    address = '1BamMXZBPLMwBT3UdyAAKy3ctGDbXNKoXk'

        # check if the address in the list
        
        if address in addresses_set:
            print("FOUND A LUCKY PAIR:\n")
            print("--------------------------------------\n")
            print(address+";"+private_key)
            print("--------------------------------------\n")
            try:
                balance = str((Service().getbalance(address))/1e8) + " BTC"
            except Exception as e:
                balance = "UNKNOWN"

            lucky_text  = "--------------------------------------\n"
            lucky_text += "FOUND A LUCKY PAIR:\n" 
            lucky_text += "PRIVATE KEY = " + private_key + "\n"
            lucky_text += "ADDRESS = " + address + "\n"
            lucky_text += "BALANCE = " + balance + "\n"
            lucky_text += "--------------------------------------\n"

            if env.SEND_EMAILS:
                try:
                    send_email(lucky_text)
                except Exception as e:
                    print("Sending email failed.")

            fl = open(env.OUT_FILE, "a")
            fl.write(lucky_text)
            fl.close()
            exit()
        else:
            print(address+";"+private_key)    


        # increment
        i = i + 1
    
    # record the number of generated private keys
    return_dict[worker_idx] = i

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    processes = []
    
    if env.NUM_INSTANCES == 0:
        inst_count = multiprocessing.cpu_count()
    else:
        inst_count = env.NUM_INSTANCES

    for i in range(inst_count):
        p= multiprocessing.Process(target=hunter, args=(env.MAX_SECONDS, i, return_dict))
        processes.append(p)
        p.start()

    total = 0
    for i in range(inst_count):
        processes[i].join()
        proc_ret = return_dict[i]
        total += proc_ret

    rate = total/env.MAX_SECONDS
    print("Tried " + str(total) + " keys in " + str(env.MAX_SECONDS) + " seconds (" + str(math.floor(rate)) + " key/s).")
