import secrets
import string

def generate_booking_reference() -> str:
    chars = string.ascii_uppercase + string.digits
    return "BK-" + "".join(secrets.choice(chars) for _ in range(6))