import base64
import re
from Crypto.Cipher import AES


class AESCBC:
    def __init__(self):
        self.mode = AES.MODE_CBC
        self.bs = 16  # block size
        self.PADDING = lambda s: s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def format_key(key):
        key_bytes = str.encode(key, 'UTF-8')
        byte_array = bytearray(16)
        length = len(key_bytes)
        if length > len(byte_array):
            length = len(byte_array)
        byte_array[0: length] = key_bytes
        return bytes(byte_array)

    def encrypt(self, text, key):
        formatted_key = self.format_key(key)
        print(f'formatted key {formatted_key}')
        generator = AES.new(formatted_key, self.mode, formatted_key)
        encrypt = generator.encrypt(self.PADDING(text))
        encrypted_str = base64.b64encode(encrypt)
        result = encrypted_str.decode()
        return result

    def decrypt(self, text, key):
        formatted_key = self.format_key(key)
        generator = AES.new(formatted_key, self.mode, formatted_key)
        text += (len(text) % 4) * '='
        decrypt_bytes = base64.b64decode(text)  # outputBase64
        meg = generator.decrypt(decrypt_bytes)
        try:
            result = re.compile('[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f\n\r\t]').sub('', meg.decode())
        except Exception:
            result = 'Decoding failed, please try again!'
        return result


if __name__ == '__main__':
    aes = AESCBC()
    shared_key = 'testkey'
    original_text = 'userid^phone^time'
    encrypted_text = 'jxQS7fhEQ6n2N2f+t51g6k0zzMeacwj4I3kZJm51ITw='

    print("\nOriginal: {0}\nEncrypted: {1}\n".format(original_text, aes.encrypt(original_text, shared_key)))
    print("Encrypted: {0}\nDecrypted: {1}".format(encrypted_text, aes.decrypt(encrypted_text, shared_key)))
