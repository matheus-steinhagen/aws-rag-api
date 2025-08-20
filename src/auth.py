# --------------------------------------------------
# src/auth.py
# --------------------------------------------------
# Este módulo implementa autentucação e autorização básica
# simulando o comportamento do AWS Cognito
#
# O que temos aqui
# - Middleware que intercepta todas as requisições HTTP e valida o JWT
# - Carregamento das chaves públicas a partir de um JWkS (JSON Web Key Set)
# - Endpoint /login que gera tokens de teste assinados localmente
# - Função utilitária para extrair roles das claims
#
# Em termos de aprendizado
# - Como autenticar usuário com JWT
# - Como interceptar claims em um JWT
# - Como processar requisições antes de chegar no handler
# - Dá gancho para como limitar permissões com base em roles

import json
import time
from pathlib import Path
from typing import List

# PyJWT → biblioteca para gerar e validar tokens JWT
import jwt #PyJWT
from jwt import PyJWTError
from jwt.algorithms import RSAAlgorithm

# FastAPI → Request permite acessar header; HTTPException retorna erros padrão
from fastapi import Request, HTTPException, APIRouter
from fastapi.security.utils import get_authorization_scheme_param

#Pydantic para validar corpo de login
from pydantic import BaseModel

# --------------------------------------------------
# Carregar JWKS (JSON Web Key Set)
# --------------------------------------------------
# AWS Cognito expõe um endpoint público com as chaves públicas do User Pool:
# https://cognito-idp.{region}.amazonaws.com/{userPoolId}/.well-known/jwks.json
# Aqui usamod uma versão local em infra/jwks.json apenas para testes
#
# Em produção
# - As chaves mudam automaticamente quando Cognito faz "key rotation"
# - A API precisa buscar e cachear as novas chaves
JWKS_PATH = Path(__file__).parent.parent / "infra" / "jwks.json"
with open(JWKS_PATH) as f:
    JWKS = json.load(f)

# Montamos um dicionário {kid -> chave pública}
# O "kid" (Key ID) está no header do Jwt e serve para escolher a chave correta
PUBLIC_KEYS = {}
for key in JWKS["keys"]:
    kid = key["kid"]
    PUBLIC_KEYS[kid] = RSAAlgorithm.from_jwk(json.dumps(key))

# --------------------------------------------------
# Middleware de autenticação JWT
# --------------------------------------------------
# Este middleware roda ANTES de qualquer handler
# Ele verifica
# - Se existe um header Authorization
# - Se é do tipo "Bearer <token>"
# - Se o token é válido, assinado pela chave pública
# - Se sim, adiciona claims em request.state.user (acessível no handler)
#
# Em termos de aprendizado
# - Como autenticar com JWT
# - Quais claims estão disponíveis no token
# - Como se intercepta requests no middleware
async def jwt_auth_middleware(request: Request, call_next):

    # Permitimos algumas rotas públicas (sem autenticação)
    if request.url.path.startswith("/v1/health") or request.url.path.startswith("/v1/auth/login"):
        return await call_next(request)

    # Extraímos o header Authorization
    auth_header = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth_header)

    # Verificamos se é do tipo "Bearer <token>"
    if not token or scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Token ausente ou esquema inválido")
    
    try:
        # Lemos o header do token sem validar para extrair o "kid"
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        # Pegamos a chave pública correspondente
        public_key = PUBLIC_KEYS.get(kid)
        if not public_key:
            raise HTTPException(status_code=401, detail="Chave pública não encontrada")
    
        # Validamos o token com a chave pública e algoritmo RS256
        payload = jwt.decode(token, public_key, algorithms=["RS256"])

        # Guardamos claims do usuários no request
        # Isso estará disponível nos handlers via request.state.user
        request.state.user = payload
    except PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {str(e)}")
    
    return await call_next(request)

# --------------------------------------------------
# Endpoint de login (mock)
# --------------------------------------------------
# Em um sistema real, o login é feito pelo Cognito
# Aqui simulamos um "issuer local": assinamos tokens com uma private.pem
#
# Em termos de aprendizado
# - Como gerar tokens JWT
# - Como incluir roles no payload (claims customizadas)
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

    # Assinamos com algoritmo RS256 e incluímos o "kid" no header
    token = jwt.encode(payload,private_key, algorithm="RS256", headers={"kid": "test-key-1"})
    return {"access_token": token}


# --------------------------------------------------
# Função utilitária para extrair roles do token
# --------------------------------------------------
# Essa função ajuda a verificar se um usuário tem permissões necessárias
# Emprodução, usaríamos isso para proteger endpoints adminstrativos, etc
def get_user_roles(claims: dict) -> List[str]:
    """
    Extrai lista de roles das claims do usuário.
    """
    return claims.get("custom:roles", [])