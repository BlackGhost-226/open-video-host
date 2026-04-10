from typing import dataclass_transform
from typing import Any
from datetime import datetime, timezone
import jwt

from jwt.exceptions import ExpiredSignatureError 
from jwt.exceptions import ImmatureSignatureError 
from jwt.exceptions import InvalidSignatureError 
from jwt.exceptions import InvalidAudienceError
from jwt.exceptions import InvalidIssuerError

class IndalidTokenError(Exception):
    pass

class MissingRequiredClaimError(IndalidTokenError): # Raised when a token's claims doesn't match.
    pass

class ExpError(IndalidTokenError): # Raised when a token’s exp claim indicates that it has expired.
    pass

class NbfOrIatInFutureError(IndalidTokenError): # Raised when a token’s nbf or iat claims represent a time in the future.
    pass

class SignatureError(IndalidTokenError): # Raised when a token’s signature doesn’t match the one provided as part of the token.
    pass

class AudError(IndalidTokenError): # Raised when a token’s aud claim does not match one of the expected audience values.
    pass

class IssError(IndalidTokenError): # Raised when a token’s iss claim does not match the expected issuer.
    pass

@dataclass_transform
class BaseToken:
    def __init__(self, token:dict[str, Any]|str, config):
        self._token: str|None = None
        self._claims: dict[str, Any]|None = None
        self.config = config

        if isinstance(token, dict):
            self._claims = dict()
            for key, value in token.items():
                self._claims[key] = value
        elif isinstance(token, str):
            self._token: str = token
    
    @property
    def token(self) -> str:
        if self._token is not None:
            return self._token
        else:
            return self.encode()
    
    @token.setter
    def token(self, value) -> None:
        self._claims = None
        self._token = value

    @token.deleter
    def token(self) -> None:
        raise

    def __getattr__(self, name: str) -> Any:
        if self._claims is not None:
            try:
                return self._claims[name]
            except KeyError:
                raise AttributeError(name) from None
        else:
            try:
                return self.decode()[name]
            except KeyError:
                raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        self._token = None
        self._claims[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self._claims[name]
        except KeyError:
            raise AttributeError(name) from None
        self._token = None
    
    def decode(self, secret: str) -> dict[str, Any]:
        options = {
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_iss": True if self.config.issuer is not None else False,
            "verify_aud": True if self.config.audience is not None else False
            }
        try:
            payload = jwt.decode(
                self._token,
                secret,
                algorithms=[self.config.algorithm],
                audience=self.config.audience,
                issuer=self.config.issuer,
                options=options
            )
        except ExpiredSignatureError:
            raise ExpError()
        except ImmatureSignatureError:
            raise NbfOrIatInFutureError()
        except InvalidAudienceError:
            raise AudError()
        except InvalidIssuerError:
            raise IssError()
        except InvalidSignatureError:
            raise SignatureError()
        self._claims = dict()
        for key, item in payload.items():
            self._claims[key] = item
        return self._claims

    def encode(self, secret: str) -> str:
        now = int(datetime.now(timezone.utc).timestamp())
        payload = self._claims
        payload["aud"] = self.config.audience
        payload["iss"] = self.config.issuer
        payload["exp"] = now + self.config.exp_seconds # TODO seconds to timestamp
        payload["iat"] = now
        payload["nbf"] = now + self.config.nbf_seconds
        self._token = jwt.encode(payload, secret, self.config.algorithm)
        return self._token

    def getUnverifiedClaims(self) -> dict:
        options = {
            "verify_signature": False,
            "verify_exp": False,
            "verify_nbf": False,
            "verify_iat": False,
            "verify_iss": False,
            "verify_aud": False
            }

        payload = jwt.decode(
                self._token,
                options=options
            )
        return payload
