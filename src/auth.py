# src/auth.py

"""
Middleware de autentificação JWT simulando AWS Cognito
Perguntas que ajuda a responder:
B2: Como autenticar / autorizar usuários (JWT)
B4: O que são claims em uma token JWT
D4: Como interceptar e processar requisições antes de chegar ao handler
"""

import json
import time
from pathlib import Path
from typing import List

import jwt #PyJWT
from pydantic import BaseModel
from fastapi import Request, HTTPException, APIRouter
from fastapi.security.utils import get_authorization_scheme_param
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm
from pathlib import Path

# carregar JWKS local (mock Cognito)
JWKS_PATH = Path(__file__).parent.parent / "infra" / "jwks.json" # AWS_JWKS_PATH = https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
with open(JWKS_PATH) as f:
    JWKS = json.load(f)

PUBLIC_KEYS = {}
for key in JWKS["keys"]:
    kid = key["kid"]
    PUBLIC_KEYS[kid] = RSAAlgorithm.from_jwk(json.dumps(key))

async def jwt_auth_middleware(request: Request, call_next):
    """
    Middleware que verifica:
    - Se existe Authorization: Bearer <token>
    - Se token é válido e assinado por uma das keys no JWKS local
    """

    # rotas públicas
    if request.url.path.startswith("/v1/health") or request.url.path.startswith("/v1/auth/login"):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth_header)

    if not token or scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token ausente ou esquema inválido")
    
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        public_key = PUBLIC_KEYS.get(kid)
        if not public_key:
            raise HTTPException(status_code=401, detail="Chave pública não encontrada")
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        request.state.user = payload # claims disponíveis para handlers
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    
    return await call_next(request)

# -------------------------
# Endpoint de login mock
# -------------------------

router = APIRouter(prefix="/v1/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str

@router.post("/login")
def login_mock(req: LoginRequest):
    """
    Gera um JWT assinado com o private.pem local para testes
    """
    private_key = Path(__file__).parent.parent / "private.pem"
    private_key = private_key.read_text()

    payload = {
        "sub": req.email.split("@")[0],
        "email": req.email,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "custom:roles": ["user"]
    }
    token = jwt.encode(payload,private_key, algorithm="RS256", headers={"kid": "test-key-1"})
    return {"access_token": token}


# -------------------------
# Função para extrair roles
# -------------------------
def get_user_roles(claims: dict) -> List[str]:
    """
    Extrai lista de roles das claims do usuário.
    """
    return claims.get("custom:roles", [])