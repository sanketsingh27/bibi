import sys

import keyring
from keyring.backends.macOS import Keyring as MacOSKeyring


SERVICE = "Bibi OpenRouter"
ACCOUNT = "api-key"


class CredentialStoreUnavailable(RuntimeError):
    pass


class MacOSCredentialStore:
    @property
    def available(self) -> bool:
        return sys.platform == "darwin" and isinstance(keyring.get_keyring(), MacOSKeyring)

    def get(self) -> str | None:
        if not self.available:
            raise CredentialStoreUnavailable
        try:
            return keyring.get_password(SERVICE, ACCOUNT)
        except Exception as error:
            raise CredentialStoreUnavailable from error

    def set(self, value: str) -> None:
        if not self.available:
            raise CredentialStoreUnavailable
        try:
            keyring.set_password(SERVICE, ACCOUNT, value)
        except Exception as error:
            raise CredentialStoreUnavailable from error

    def delete(self) -> None:
        if not self.available:
            raise CredentialStoreUnavailable
        try:
            if keyring.get_password(SERVICE, ACCOUNT) is not None:
                keyring.delete_password(SERVICE, ACCOUNT)
        except Exception as error:
            raise CredentialStoreUnavailable from error
