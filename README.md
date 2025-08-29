# awsProject

## Descrição
API FastAPI que simula autenticação AWS Cognito (JWT), integra um provider LLM mock e implementa um pipeline RAG (Retrieval-Augmented Generation) básico.
O projeto é voltado para testes, aprendizado de arquitetura de APIs e demonstração de boas práticas de backend.

## Funcionalidades principis
**Autenticação JWT simulando AWS Cognito:**
- Geração de tokens via endpoint /v1/auth/login.
- Middleware valida tokens e adiciona claims do usuário (request.state.user) aos handlers.

**Pipeline RAG básico:**
- Busca contexto (dummy) baseado no prompt.
- Enriquecimento do prompt antes de gerar resposta.

**LLM MockProvider:**
- Simula respostas de modelos de linguagem (GPT, Bedrock) de forma assíncrona.
- Permite testar endpoints sem custo de APIs externas.

**Histórico em DynamoDB (simulado):**
- Cada geração é salva em uma tabela DynamoDB (mock via `moto`).
- Endpoint `/v1/history` lista histórico do usuário autenticado.

**Boas práticas de API:**
- Versionamento (`/v1`).
- Healthcheck (`/v1/health`).
- Logging estruturado.
- Testes automatizados.
- Idempotência, circuit breaker e retry.

## Estrutura
```bash
src/         # Código principal
    main.py          # Configuração da app FastAPI, routers e endpoints
    auth.py          # Middleware JWT + login mock
    providers/       # MockProvider e interface base de LLMs
    utils/           # Logging, retry, circuit breaker, idempotency
infra/       # JWKS e chaves privadas de teste
tests/       # Testes automatizados
scripts/     # Scripts utilitários (ex.: gerar token JWT)
```

## Como rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
uvicorn src.main:app --reload
```
## Login (gerar token JWT de teste)
```bash
curl -X POST http://127.0.0.1:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "teste@example.com"}'
```
Copie o valor de access_token retornado.

## Testar endpoints
```bash
# Health
curl http://127.0.0.1:8000/v1/health

# Generate (protegido)
TOKEN=<COLE_SEU_TOKEN_AQUI>
curl -X POST http://127.0.0.1:8000/v1/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: my-unique-key" \
  -d '{"prompt":"Como funciona RAG?"}'
```
- Gera texto a partir do prompt.
- Simula uso de LLM + contexto RAG.
- Suporta idempotência (mesmo request não é processado duas vezes).
- Implementa circuit breaker e retry para resiliência.
- Retorna:
```json
  "generated": "Simulação: Como funciona RAG? - resposta fictícia",
  "context": ["RAG é Retrieval Augmented Generation...", "Busca contexto + gera resposta"],
  "user": {"sub":"teste","email":"teste@example.com","custom:roles":["user"]},
  "request_id": "uuid-gerado"
```

## Alternativa: Gerar token via script
Se preferir, você também pode gerar um token usando o script
```bash
python scripts/generate_token.py > token.txt
```
## Conceitos implementados
- JWT e middleware de autenticação → protege endpoints e adiciona claims do usuário.
- RAG básico → demonstra como enriquecer prompts com contexto.
- Mock LLM → permite treino sem dependências externas.
- Idempotência → evita processamento duplicado em endpoints críticos.
- Circuit breaker + retry → garante resiliência a falhas temporárias.
- Logging estruturado → facilita auditoria e debugging.
