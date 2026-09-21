"""Encrypt/decrypt account credentials at rest."""

from cryptography.fernet import Fernet


class SecretBox:
    """Wraps one Fernet key for encrypting credentials in the database."""

    def __init__(self, key: str) -> None:
        """Build a box from a urlsafe-base64 Fernet key string."""
        self._fernet = Fernet(key.encode("utf-8"))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt `plaintext` into a string safe to store in a column."""
        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return encrypted.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a value previously returned by `encrypt`."""
        return self._fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
