from dataclasses import dataclass
from datetime import datetime, timezone
from hmac import compare_digest
from uuid import uuid4
import jwt

class IndalidTokenError(Exception):
    pass

class MissingRequiredClaimError(IndalidTokenError):
    pass

class JWTToken:
    def __init__(self, token: dict):
        self.claims = {}
        self.jwtId = self.addClaim(token.get("jti"), "jti")
        self.issuer = token.get("iss")
        self.audience = token.get("aud")
    
    def __repr__(self):
        return f"{self.__class__}: {str(self.claims)}"

    def addClaimOrNone(self, token: dict, claimName: str):
        return self.addClaim(token.get(claimName), claimName)

    def addClaimOrError(self, token: dict, claimName: str):
        try:
            return self.addClaim(token[claimName], claimName)
        except KeyError as e:
            raise MissingRequiredClaimError(e)
    
    def addClaim(self, value, claim):
        if value is not None:
            self.claims[claim] = value
        return value


class AccessToken(JWTToken):
    def __init__(self, token: dict):
        super().__init__(token)
        self.jwtId = self.addClaimOrError(token, "jti")
        self.userId = self.addClaimOrError(token, "sub")
        self.csrf = self.addClaimOrError(token, "csrf")

class RefreshToken(JWTToken):
    def __init__(self, token: dict):
        super().__init__(token)
        self.jwtId = self.addClaimOrError(token, "jti")
        self.csrf = self.addClaimOrError(token, "csrf")

@dataclass
class JWTDecodeConfig:
    algorithm: str
    exp_seconds: int
    issuer: str = None
    audience: str = None
    nbf_seconds: int = 0

accessTokenConfig = JWTDecodeConfig(algorithm="RS256", 
                                    issuer="auth.myapp.internal", 
                                    audience="all",
                                    exp_seconds=900)

refreshTokenConfig = JWTDecodeConfig(algorithm="RS256", # HS256
                                     issuer="auth.myapp.internal", 
                                     audience="auth",
                                     exp_seconds=604800)

def decode(encoded_token: str, secret: str, token: type[JWTToken], config: JWTDecodeConfig) -> JWTToken:
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_iss": True if config.issuer is not None else False,
        "verify_aud": True if config.audience is not None else False
        }

    payload = jwt.decode(
            encoded_token,
            secret,
            algorithms=[config.algorithm],
            audience=config.audience,
            issuer=config.issuer,
            options=options
        )
    return token(payload)

def encode(secret: str, token: JWTToken, config: JWTDecodeConfig) -> str:
    now = int(datetime.now(timezone.utc).timestamp())
    payload = token.claims
    payload["aud"] = config.audience
    payload["iss"] = config.issuer
    payload["exp"] = now + config.exp_seconds # TODO seconds to timestamp
    payload["iat"] = now
    payload["nbf"] = now + config.nbf_seconds
    return jwt.encode(payload, secret, config.algorithm)

def getUnverifiedClaims(encoded_token: str) -> dict:
    options = {
        "verify_signature": False,
        "verify_exp": False,
        "verify_nbf": False,
        "verify_iat": False,
        "verify_iss": False,
        "verify_aud": False
        }

    payload = jwt.decode(
            encoded_token,
            options=options
        )
    return payload
