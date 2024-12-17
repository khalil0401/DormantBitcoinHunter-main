import ecdsa.util
import hashlib
import base58
from ripemd.ripemd160 import ripemd160
 
private_key = "18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725"
# Crear la clave privada y pública 
sk = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
vk = sk.get_verifying_key()
 
# Obtener la clave pública comprimida
public_key_compressed = "02" + vk.pubkey.point.x().to_bytes(32, byteorder="big").hex()
 

 
# construcion de unaddress BTC
# https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses
 
sha256_hash = hashlib.sha256(bytes.fromhex(public_key_compressed)).digest()
ripemd160_hash = ripemd160(sha256_hash)
middle_man = b'\00' + ripemd160_hash
checksum = hashlib.sha256(hashlib.sha256(middle_man).digest()).digest()[:4]
binary_addr = middle_man + checksum
addr = base58.b58encode(binary_addr)
 
print("private_key", private_key)
print("public_key (compressed)", public_key_compressed)

print("primo EDCSA",vk.pubkey.curve.p())
print ("BTC address: ",  addr.decode())
