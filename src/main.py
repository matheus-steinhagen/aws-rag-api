# --------------------------------------------------
# main.py
# --------------------------------------------------
# Este arquivo ŕ o "coração" do projeto
# É aqui quer
# - Instanciamos a aplicação FastAPI
# - Configuramos middlewares (ex. autenticação JWT)
# - Definimos endepoints versionados (/v1)
# - Expomos a rota principal /generate que usa o MockProvider
# --------------------------------------------------

import random

# FastAPI → framework que usamos para expor endpoints HTTP
# APIRouter → nos permite agrupar rotas com prefixos
# Request → usado para acessar dados da requisição
# Header → permite ler cabeçalhos HTTP como "Idempotency-Key"
# HTTPException + status → usados para retornar erros padronizados
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Header, status

# Pydantic é usado para validar dados de entrada / saída da API
# Field → adicoina restrições (ex. prompt não pode ser vazio)
from pydantic import BaseModel, Field

# Tipos do Python (List, Dict, etc.) para deixar o código mais legível
from typing import List, Dict, Any, Optional

# uuid gera identificadores únicos (úteis para request_id e tracing)
from uuid import uuid4

# Middleware de autenticação JWT → simula AWS Cognito
# Importamos também o router de /auth (que expõe endpoint de login)
from src.auth import jwt_auth_middleware, router as auth_router

# MockProvider é um "LLM falso" que responde de forma simulada
# Assim conseguimos treinar sem gastar com modelos reais (Bedrock / OpenAI)
from src.providers.mock_provider import MockProvider

# Funções utilitárias: sanitizar prompt (remoção PII) + configurar logging
from src.utils.sanitize import sanitize_prompt_for_logging
from src.utils.logging_config import configure_logging
from src.utils.idempotency import InMemoryIdempotencyStore
from src.utils.retry import retry_async
from src.utils.circuit_breaker import CircuitBreaker

# Configuramos logging global → todos os logs seguem o mesmo formato
configure_logging()
import logging
log = logging.getLogger("awsProject.main")

# --------------------------------------------------
# Instancia a aplicação FastAPI
# --------------------------------------------------
# Aqui damos nome a versão do projeto
# Essas informaçõess aparecem automaticamente no Swagger UI
app = FastAPI(title = "awsProject", version = "0.1.0")

# --------------------------------------------------
# Registra o middleware e routers
# --------------------------------------------------
# Middleware de autenticação JWT
# Ele roda ANTES de qualuqer endpoint e bloqueia restrições sem token válido
app.middleware("http")(jwt_auth_middleware)

# Router de autentificação (rotas /v1/auth/*)
# Permite login e geração de tokens JWT de teste
app.include_router(auth_router)

# --------------------------------------------------
# Definição de rotas versionadas
# --------------------------------------------------
# Criamos um "subconjunto de rotas" com prefixo v1
# Versionamento é prática comum em APIs
v1 = APIRouter(prefix="/v1")

# Healthcheck → usado por Kubernetes / AWS para saber se o serviço está vivo
# Sem isso, a empresa não consegue escalar ou reiniciar containers automaticamente
@v1.get("/health")
async def health():
    """
    Endpoint de healthcheck
    Útil para readniess/liveness probes e para demonstrar rota versionada
    """
    return {"status": "ok"}

# --------------------------------------------------
# Definição de payloads (Resquest e Response)
# --------------------------------------------------
# Classe para validar entrada do usuário no endpoint /generate
# - prompt é obrigatório, com tamanho entre 1 e 4000 caracteres
# Isso previne erros e abusos (ex. prompts enormes que podem travar o sistema)
class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000)

# Classe que define a estrutura da resposta
# Ajuda a mantes consistência e melhora a documentação da API
class GenerateResponse(BaseModel):
    generated: str
    context: List[str]
    user: Dict[str, Any]
    request_id: str


# --------------------------------------------------
# Mock provider e função de contexto
# --------------------------------------------------
mock_provider = MockProvider()

# --------------------------------------------------
# Infra de resiliência e idempotência (escopo do processo)
# --------------------------------------------------
idempotency_store = InMemoryIdempotencyStore(ttl_seconds=600) # 10 minutos
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time=10.0)

def retrieve_context(prompt: str):
    """
    Função simulando a etada "RAG" (Retrieval Augmented Generation)
    Se o prompt mencionar "rag", retornamos um contexto fixo
    Caso contrário, retornamos "Sem contexto encontrado"

    Em termos de aprendizado
    - Isso tem a ver com enriquecer LLMs com contexto
    - Mostra como funcionaria um retrieval simples
    """
    p = prompt.strip().lower()
    if "rag" in p:
        return [
            "RAG é Retrieval Augmented Generation...",
            "Busca contexto + gera resposta"
        ]
    return ["Sem contexto encontrado"]

# --------------------------------------------------
# Endpoint /generate
# --------------------------------------------------
# Este é o endpoint principal da aplicação
# - Protegido por JWT (precisa de token válido)
# - Loga informações de cada chamada (request_id, usuário, prompt)
# - Sanitiza prompt para não expor dados sensíveis em logs
# - Adiciona suporte a Idempotency-Key
# - Responde com texto gerado pelo MockProvider
@v1.post("/generate", response_model=GenerateResponse)
async def generate(
    req: GenerateRequest,
    request: Request,
    response: Response,
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key")
):
    """
    Endpoint /v1/generate
    - Gera texto a partor de um prompt, simulando uso de LLM
    - Mostra como aplicar boas práticas de APIs (idempotência, logging, request_id)
    """
    user_claims = getattr(request.state, "user", {})
    if not user_claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid token")

    # Gera identificador único para rastrear a requisição
    request_id = str(uuid4())

    # Sanitiza prompt (remove emails / tokens antes de logar)
    sanitized = sanitize_prompt_for_logging(req.prompt)

    # Loga a chamada → útil para auditoria, debugging e tracing
    log.info(
        "generate called request_id=%s user=%s prompt=%s idempotency_key=%s",
        request_id,
        user_claims.get("sub"),
        sanitized,
        idempotency_key
    )

    # -------------------------
    # Idempotency-Key
    # -------------------------
    lock = None
    incoming_body = req.model_dump()  # pydantic v2; se v1, use req.dict()
    incoming_hash = idempotency_store.body_hash(incoming_body)

    if idempotency_key:
        # lock por chave para evitar corrida entre requisições simultâneas
        lock = await idempotency_store.acquire_lock(idempotency_key)
        cached = idempotency_store.get_entry(idempotency_key)
        if cached:
            if cached["body_hash"] != incoming_hash:
                #mesma chave com corpo diferente -> 409
                if lock:
                    lock.release()
                raise HTTPException(
                    status_code = status.HTTP_409_CONFLICT,
                    detail = "Idempotency-Key reuse with different request body"
                )
            # replay: retorna a mesma resposta sem reprocessar
            response.headers["Idempotency-Replay"] = "true"
            log.info("idempotent replay request_id=%s key=%s", request_id, idempotency_key)
            if lock:
                lock.release()
            return cached["data"]

    # Simula busca de contexto (mini-RAG)
    context = retrieve_context(req.prompt) # RAG dummy → busca contexto estático

    # -------------------------
    # Circuit breaker: bloqueia se o upstream estiver ruim
    # -------------------------
    allowed = await circuit_breaker.allow_request()
    if not allowed:
        log.warning("circuit open request_id=%s", request_id)
        raise HTTPException(
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
            detail = f"Upstream LLM temporarily unavailable (circuit open, request_id={request_id})"
        )
    
    # Para treino: se o prompt contiver 'fail', simulamos falha transitória
    should_fail = "fail" in req.prompt.lower() or "falha" in req.prompt.lower()

    async def call_provider():
        if should_fail and random.random() < 0.7:
            raise RuntimeError("Injected transient failure (simulated)")
        return await mock_provider.generate_text(
            f"Contexto: {' '.join(context)} | Pergunta: {req.prompt}"
        )
    
    try:
        generated_text = await retry_async(
            call_provider,
            attempts=3,
            min_delay=0.2,
            max_delay=1.5,
            exceptions=(Exception,),
            jitter=True
        )
        await circuit_breaker.on_success()
    except Exception:
        await circuit_breaker.on_failure()
        log.exception("Provider error (after retry) request_id=%s", request_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"upstream error (request_id={request_id})"
        )

    # Montamos a resposta final
    result = {
        "generated": generated_text,
        "context": context,
        "user": user_claims,
        "request_id": request_id
    }

    if idempotency_key:
        idempotency_store.put(idempotency_key, incoming_body, result)
        response.headers["Idempotency-Replay"] = "false"
        if lock:
            lock.release()

    return result

# --------------------------------------------------
# Registrar router no app principal
# --------------------------------------------------
app.include_router(v1)