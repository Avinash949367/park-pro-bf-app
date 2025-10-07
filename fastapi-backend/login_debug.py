import bcrypt

# Stored bcrypt hash from DB (example)
# stored_hash = b"$2b$10$fw0t0EFS2v9YI59jr0rvWOFYGaubcggcVw.paUgVfNh/ouwl7kGEu"


# Password input by user
input_password = "AVINASH@2005.SV"

# Encode input password to bytes
password_bytes = input_password.encode('utf-8')

# Check password
if bcrypt.checkpw(password_bytes, stored_hash):
    print("Password match: Login successful")
else:
    print("Password does not match: Login failed")
