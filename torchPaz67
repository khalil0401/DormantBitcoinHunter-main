import torch
import hashlib

# إعداد الجهاز (GPU أو CPU حسب التوافر)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# النطاق المطلوب
minRange = int("40000000000000000", 16)
maxRange = int("7ffffffffffffffff", 16)

# العنوان المطلوب التحقق منه
target_address = "1BY8GQbnueYofwSuFAT3USAhGjPrkxDdW9"

# دالة تحويل المفتاح الخاص إلى العنوان (محاكاة بسيطة)
def generate_address(private_key):
    sha256_hash = hashlib.sha256(private_key.to_bytes(32, byteorder="big")).hexdigest()
    address = sha256_hash[:34]  # محاكاة عشوائية لمطابقة العناوين
    return address

# استخدام الـ GPU لتوليد المفاتيح والتحقق منها
while True:
    private_key_value = torch.randint(minRange, maxRange, (1,), device=device, dtype=torch.int64).item()

    address = generate_address(private_key_value)

    if address == target_address:
        print("\nMatch Found!")
        print(f"Private Key: {hex(private_key_value)}")
        break
