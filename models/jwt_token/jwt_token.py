from hmac import compare_digest
import jwt
import uuid
from datetime import datetime
from datetime import timedelta
from datetime import timezone
import json

class JWTException(Exception):
    """
    Base except which all flask_jwt_extended errors extend
    """

    pass

class JWTDecodeError(JWTException):
    """
    An error decoding a JWT
    """

    pass

class CSRFError(JWTException):
    """
    An error with CSRF protection
    """

    pass

class JWTTokenConfig:
    def __init__(self, key: str, raw: dict):
        self.name = key
        self.algorithm: str = raw[key]["algorithm"]
        self.issuer: str = raw[key]["issuer"]
        self.audience: str = raw[key]["audience"]
        self.token_exp_seconds: int = raw[key]["token_exp_seconds"]
        self.leeway_seconds: int = raw[key]["leeway_seconds"]
        self.required_claims: list = raw[key]["required_claims"]
        self.optional_claims: list = raw[key]["optional_claims"]
        self.enforce_issuer: bool = raw[key]["enforce_issuer"]
        self.enforce_audience: bool = raw[key]["enforce_audience"]
        self.csrf_protection: bool = raw[key]["csrf_protection"]

        for param in ["exp", "iat", "nbf", "jti", "auth_version"]:
            if param not in self.required_claims:
                self.required_claims.append(param)
        
        if self.enforce_issuer:
            self.required_claims.append("iss")
        
        if self.enforce_audience:
            self.required_claims.append("aud")
        
        if self.csrf_protection:
            self.required_claims.append("csrf")

class JWTGlobalConfig:
    def __init__(self, raw: dict):
        self.csrf_protection_header_name: str = raw["csrf_protection_header_name"]
        self.current_auth_version: int = raw["auth_version"]

class EncodeOutput:
    def __init__(self, token, payload):
        self.token = token
        self.payload = payload

class JWTManager:
    def __init__(self):
        with open("./jwt_token/config.json", "r") as file:
            config_json = json.load(file)
        
        tokens_config = config_json["jwt_tokens"]
        self.jwt_configs = {}
        for key in tokens_config:
            self.jwt_configs[key] = JWTTokenConfig(raw=tokens_config, key=key)

        self.global_jwt_config = JWTGlobalConfig(raw=config_json)
    
    def get_token_config(self, key: str) -> JWTTokenConfig:
        return self.jwt_configs.get(key)

    def encode_jwt(self, secret: str, config: JWTTokenConfig, fresh: bool = False, jti: str = str(uuid.uuid4()), **kwargs) -> EncodeOutput:
        now = datetime.now(timezone.utc).timestamp()

        payload = {
            "jti": jti,
            "nbf": int(now),
            "exp": int(now + timedelta(seconds=config.token_exp_seconds).seconds),
            "iat": int(now),
            "auth_version": int(self.global_jwt_config.current_auth_version)
        }

        if config.csrf_protection:
            payload["csrf"] = str(uuid.uuid4())

        if config.enforce_audience:
            payload["aud"] = config.audience

        if config.enforce_issuer:
            payload["iss"] = config.issuer
    
        if "fresh" in config.required_claims:
            payload["fresh"] = fresh

        if kwargs:
            payload.update(kwargs)

        return EncodeOutput(jwt.encode(payload, secret, config.algorithm), payload)

    def decode_jwt(self, encoded_token: str, secret: str, config: JWTTokenConfig, csrf_value: str) -> dict:
        now = int(datetime.now(timezone.utc).timestamp())

        options = {
        "verify_signature": True,
        "verify_exp": True,
        "verify_nbf": True,
        "verify_iat": True,
        "verify_iss": config.enforce_issuer,
        "verify_aud": config.enforce_audience,
        }

        payload = jwt.decode(
            encoded_token,
            secret,
            algorithms=config.algorithm,
            audience=config.audience if config.enforce_audience else None,
            issuer=config.issuer if config.enforce_issuer else None,
            leeway=config.leeway_seconds,
            options=options,
        )

        for claim in config.required_claims:
            if claim not in payload:
                raise JWTDecodeError(f"Missing claim: {claim}")
    
        if payload["iat"] > now + config.leeway_seconds:
            raise JWTDecodeError("iat is in the future")
    
        if payload["auth_version"] < self.global_jwt_config.current_auth_version:
            raise JWTDecodeError("Token revoked globally")
    
        allowed = set(config.required_claims) | set(config.optional_claims)
        unknown = set(payload) - allowed
        if unknown:
            raise JWTDecodeError("Unknown JWT claims", unknown)

        if config.csrf_protection:
            if "csrf" not in payload:
                raise JWTDecodeError("Missing claim: csrf")
            if not compare_digest(payload["csrf"], csrf_value):
                raise CSRFError("CSRF double submit tokens do not match")

        return payload
