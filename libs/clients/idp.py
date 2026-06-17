import requests
from dataclasses import dataclass


@dataclass
class Tokens:
    refresh: str
    refresh_exp_seconds: int
    access: str
    access_exp_seconds: int
    csrf: str

    def __repr__(self):
        return str(self.__dict__)

class Client:
    def __init__(self, base_url, expected_issuer, expected_audience):
        self.baseUrl = base_url
        self.expectedIssuer = expected_issuer
        self.expectedAudience = expected_audience
        self.csrfHeaderName = "X-CSRF"
        self.accessCookieName = "access-c"
        self.refreshCookieName = "refresh-c"
        self._IdPPublicKey = None

    @property
    def IdPPublicKey(self):
        if self._IdPPublicKey is None:
            self._IdPPublicKey = requests.get(url=self.baseUrl+"/public_key").json()["key"]
        return self._IdPPublicKey
    
    def login(self, email, passwd, agent):
        response = requests.post(self.baseUrl+"/login", json={"email": email,
                                                   "password": passwd,
                                                   "user_agent": agent})
        if response.status_code == 200:
            json = response.json()
            return Tokens(refresh=json["refresh_token"], 
                      access=json["access_token"], 
                      refresh_exp_seconds=json["refresh_exp_seconds"],
                      access_exp_seconds=json["access_exp_seconds"],
                      csrf=json["csrf"])
        else:
            return None

    def refresh(self, refresh_token, last_access_jti):
        response = requests.post(self.baseUrl+"/refresh", json={"refresh_token": refresh_token,
                                                     "last_access_jti": last_access_jti})
        if response.status_code == 200:
            json = response.json()
            return Tokens(refresh=json["refresh_token"], 
                      access=json["access_token"], 
                      refresh_exp_seconds=json["refresh_exp_seconds"],
                      access_exp_seconds=json["access_exp_seconds"],
                      csrf=json["csrf"])
        else:
            return None
            

    def freshRefresh(self, refresh_token, last_access_jti, passwd):
        response = requests.post(self.baseUrl+"/refresh", json={"refresh_token": refresh_token,
                                                     "last_access_jti": last_access_jti,
                                                     "password": passwd})
        if response.status_code == 200:
            json = response.json()
            return Tokens(refresh=json["refresh_token"], 
                      access=json["access_token"], 
                      refresh_exp_seconds=json["refresh_exp_seconds"],
                      access_exp_seconds=json["access_exp_seconds"],
                      csrf=json["csrf"])
        else:
            return None

    def RevokeTokenPair(self, refresh_token):
        requests.get(self.baseUrl+f"/revoke/{refresh_token}")
    
    def CheckIfAccessTokenIsRevoked(self, access_token):
        response = requests.get(self.baseUrl+f"/check_revocation/{access_token}")
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
    
    def createUser(self, name, email, passwd):
        response = requests.post(self.baseUrl+"/user", json={"username": name,
                                                  "email": email,
                                                  "password": passwd})
        return response.json()["user_id"]