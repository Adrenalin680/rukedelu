import random

# Временное хранилище кодов
verification_codes = {}

def generate_code():
    """Генерирует 6-значный код подтверждения"""
    return str(random.randint(100000, 999999))

def send_verification_code(phone_number):
    """Отправляет код (демо-версия - просто генерирует и сохраняет)"""
    code = generate_code()
    verification_codes[phone_number] = code
    print(f"[DEMO] Код подтверждения для {phone_number}: {code}")
    return True, code

def verify_code(phone_number, code):
    """Проверяет введенный код"""
    stored_code = verification_codes.get(phone_number)
    if stored_code and stored_code == code:
        del verification_codes[phone_number]
        return True
    return False
