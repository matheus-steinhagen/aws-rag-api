# main.py

# -- FastAPI skeleton com rotas versionadas /v1 --
from fastapi import FastAPI, APIRouter, Request
from pydantic import BaseModel
from src.auth import jwt_auth_middleware, router as auth_router
from src.providers.mock_provider import MockProvider

# Instancia a FastAPI
app = FastAPI(title = "awsProject", version = "0.1.0") #instancia FastAPI

# Registra o middleware de autentificação
app.middleware("http")(jwt_auth_middleware)

app.include_router(auth_router)

# router versionado v1 (bom para versionamento e rollouts canary)
v1 = APIRouter(prefix="/v1")

# health endpoint simples
@v1.get("/health")
async def health():
    """
    Endpoint de healthcheck
    Útil para readniess/liveness probes e para demonstrar rota versionada
    """
    return {"status": "ok"}

# payload example para /generate (por enquanto só o esqueleto)
class GenerateRequest(BaseModel):
    prompt: str

mock_provider = MockProvider()

def retrieve_context(prompt: str):
    docs = {
        "Como funciona RAG?": ["RAG é Retrieval Augmented Generation...", "Busca contexto + gera resposta"],
        "default": ["Sem contexto encontrado"]
    }
    return docs.get(prompt, docs["default"])

# Endpoint protegido por JWT
@v1.post("/generate")
async def generate(req: GenerateRequest, request: Request):
    """
    Endpoint /v1/generate - esqueleto.
    Atualmente usa MockProvider para gerar texto de forma simulada
    Em checkpoints seguintes vamos:
    - aplicar RAG e chamar LLMProvider real
    - guardar histórico em DynamoDB-like repo
    """
    user_claims = request.state.user
    context = retrieve_context(req.prompt)
    generated_text = await mock_provider.generate_text(f"Contexto: {' '.join(context)} | Pergunta: {req.prompt}")
    return{
        "generated": generated_text,
        "context": context,
        "user": user_claims}

# registrar router no app
app.include_router(v1)