import secrets

from django.contrib.auth.hashers import check_password, make_password


OTP_LENGTH = 6


def generate_otp_code():
        
    minimum = 10 ** (OTP_LENGTH - 1)
    maximum = (10 ** OTP_LENGTH) - 1

    return str(
        secrets.randbelow(maximum - minimum + 1) + minimum
    )


def hash_otp_code(code):
   
    return make_password(code)


def verify_otp_code(code, code_hash):
    
    return check_password(code, code_hash)
