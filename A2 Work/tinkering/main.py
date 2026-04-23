import datetime
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import socket

# Information on public and private RSA key generation obtained from this website: https://dev.to/aaronktberry/generating-encrypted-key-pairs-in-python-69b

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 65335

print("Generating RSA private and public keys for digital signatures...")

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

with open("public_key.pem", "wb") as f:
    f.write(public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1
    ))
    
with open("private_key.pem", "wb") as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))
    
# Certificate creation obtained via prompting Google Gemini for how to use the x509 and cryptography packages: https://share.google/aimode/kvsn5n4SOsu2err3u
    
print("Generating x509 certificate to transmit public key to server")

subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"MA"),
    # Add other attributes as needed
    x509.NameAttribute(NameOID.COMMON_NAME, u"Kyle Schmottlach"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    public_key
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.now(datetime.timezone.utc)
).not_valid_after(
    datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=365)
).sign(private_key, hashes.SHA256())

with open("certificate.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
    
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(5.0)
    
    connection_successful = True
    
    try:
        print(f"Attempting connection to {SERVER_HOST}, {SERVER_PORT}")
        s.connect((SERVER_HOST, SERVER_PORT))
    except ConnectionRefusedError:
        print("Server is down or port is closed.")
        connection_successful = False
    except socket.timeout:
        print("Connection timed out.")
        connection_successful = False
    except socket.gaierror:
        print("Hostname could not be resolved.")
        connection_successful = False
    except OSError as e:
        print(f"Network error: {e}")
        connection_successful = False
    
    if connection_successful:
        s.sendall(cert.public_bytes(serialization.Encoding.PEM))