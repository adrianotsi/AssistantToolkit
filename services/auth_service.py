import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import os
from pydantic import BaseModel

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")
SECRET_KEY = os.getenv("SECRET_KEY")
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# class ClientCredentials(BaseModel):
#     userName: str
#     password: str

class JWTBearer:
    def __init__(self, auto_error: bool = True):
        self.auto_error = auto_error

    async def __call__(self, token: str = Depends(oauth2_scheme)):
        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=403,
                    detail="Token não fornecido"
                )
            return None

        if not self.verify_jwt(token):
            raise HTTPException(
                status_code=403,
                detail="Token inválido ou expirado"
            )
        return token

    def verify_jwt(self, token: str) -> bool:
        try:
            jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.InvalidTokenError:
            return False

def create_jwt(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)):
    to_encode = data.copy()
    expire = datetime.now() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=JWT_ALGORITHM)
