from cryptography .fernet import Fernet

class CustomEncryption :
    def __init__ (self, key = '') :
        self .own_cipher = Fernet (key)
        self .remote_cipher = self .own_cipher
        self .encrypt_count = 0
        self .decrypt_count = 0

    def encrypt (self, data) :
        self .encrypt_count += 1
        return self .own_cipher .encrypt (data)

    def decrypt (self, data) :
        self .decrypt_count += 1
        return self .remote_cipher .decrypt (data)

    def get_new_key (self) :
        return Fernet .generate_key ()

    def update_own_cipher (self, key) :
        self .encrypt_count = 0
        self .own_cipher = Fernet (key)

    def update_remote_cipher (self, key) :
        self .decrypt_count = 0
        self .remote_cipher = Fernet (key)

