import os
import math
import time
import ecdsa
import sys
import smtplib
import hashlib
import base58
import multiprocessing
import ssl
from email.message import EmailMessage
from bitcoinlib.services.services import Service
import pyopencl as cl
import numpy as np
import addresses
import env

# Send Email
def send_email(lucky_text):
    text = env.email_text + "\n" + lucky_text
    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = env.subject
    msg['From'] = env.SEND_FROM
    msg['To'] = env.SEND_TO
    context = ssl.create_default_context()
    s = smtplib.SMTP(env.SMTP_HOST, env.SMTP_PORT)
    s.starttls(context=context)
    s.login(env.USER, env.PASS)
    s.send_message(msg)
    s.quit()
    print('Lucky Email sent!')

def create_btc_address(private_key):
    private_key_bytes = bytes.fromhex(private_key)
    sha256 = hashlib.sha256(private_key_bytes).digest()
    ripemd160 = hashlib.new('ripemd160', sha256).digest()

    versioned_hash = b'\x00' + ripemd160
    checksum = hashlib.sha256(hashlib.sha256(versioned_hash).digest()).digest()[:4]
    binary_address = versioned_hash + checksum
    return base58.b58encode(binary_address).decode('utf-8')

def hunter(num_seconds, worker_idx, return_dict):
    addresses_set = set(addresses.addresses)

    # إعداد OpenCL
    platform = cl.get_platforms()[0]
    device = platform.get_devices()[0]
    context = cl.Context([device])
    queue = cl.CommandQueue(context)

    num_keys = 1000000
    keys_buffer = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=num_keys * 32)
    hashed_keys_buffer = cl.Buffer(context, cl.mem_flags.WRITE_ONLY, size=num_keys * 32)

    # الكيرنلات OpenCL
    kernel_code = """
    __kernel void generate_private_keys(__global uchar *keys, const int num_keys) {
        int idx = get_global_id(0);
        if (idx < num_keys) {
            uint seed = idx;
            for (int i = 0; i < 32; i++) {
                keys[idx * 32 + i] = seed & 0xFF;
                seed >>= 8;
            }
        }
    }
    __kernel void compute_sha256(__global uchar *private_keys, __global uchar *hashed_keys, const int num_keys) {
        int idx = get_global_id(0);
        if (idx < num_keys) {
            uint sum = 0;
            for (int i = 0; i < 32; i++) {
                sum += private_keys[idx * 32 + i];
            }
            for (int i = 0; i < 32; i++) {
                hashed_keys[idx * 32 + i] = (uchar)(sum + i);
            }
        }
    }
    """

    program = cl.Program(context, kernel_code).build()

    i = 0
    start = time.time()

    while (time.time() - start) < num_seconds:
        # تنفيذ الكيرنلات OpenCL
        program.generate_private_keys(queue, (num_keys,), None, keys_buffer, np.int32(num_keys))
        program.compute_sha256(queue, (num_keys,), None, keys_buffer, hashed_keys_buffer, np.int32(num_keys))

        host_keys = np.empty((num_keys, 32), dtype=np.uint8)
        cl.enqueue_copy(queue, host_keys, keys_buffer)

        for key in host_keys:
            key_str = ''.join([f"{b:02x}" for b in key])
            btc_address = create_btc_address(key_str)
            print(f"{btc_address};{key_str}")

            if btc_address in addresses_set:
                print(f"FOUND A LUCKY PAIR:")
                print(f"Bitcoin Address: {btc_address}")
                private_hex = key.hex()
                print(f"Private Key: {private_hex}")

                try:
                    balance = str(Service().getbalance(btc_address)) + " BTC"
                except Exception:
                    balance = "UNKNOWN"

                lucky_text = f"""
                --------------------------------------
                FOUND A LUCKY PAIR:
                Bitcoin Address = {btc_address}
                Private Key = {private_hex}
                Balance = {balance}
                --------------------------------------
                """
                if env.SEND_EMAILS:
                    try:
                        send_email(lucky_text)
                    except Exception:
                        print("Email sending failed.")

                with open(env.OUT_FILE, "a") as file:
                    file.write(lucky_text)

                return_dict[worker_idx] = i
                return

        i += 1

    return_dict[worker_idx] = i

if __name__ == '__main__':
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    processes = []

    inst_count = multiprocessing.cpu_count() if env.NUM_INSTANCES == 0 else env.NUM_INSTANCES

    for i in range(inst_count):
        p = multiprocessing.Process(target=hunter, args=(env.MAX_SECONDS, i, return_dict))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    total_generated = sum(return_dict.values())
    rate = total_generated / env.MAX_SECONDS
    print(f"Tried {total_generated} Bitcoin addresses in {env.MAX_SECONDS} seconds, at {rate:.2f} addresses per second.")
