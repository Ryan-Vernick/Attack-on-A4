import socket
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

HOST = "127.0.0.1"
PORT = 65335

packets: list[bytes] = []

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print("Waiting for connection...")
    conn, addr = s.accept()
    with conn:
        print("Connected to client! Receiving certificate...")
        while True:
            recv_data = conn.recv(1024)
            if not recv_data:
                break
            packets.append(recv_data)
            
        cert_data = b"".join(packets)
        cert = x509.load_pem_x509_certificate(cert_data)
        
        print(f"Certificate:\n{cert.public_bytes(serialization.Encoding.PEM)}")
        
        public_key = cert.public_key()
        
        try:
            public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                cert.signature_hash_algorithm,
            )
            print("Verification succeeded, certificate is authentic")
        except Exception as e:
            print(f"Verification failed: {e}")
        
        print(f"Public key:\n{public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.PKCS1
        )}")
        