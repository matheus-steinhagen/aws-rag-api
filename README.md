# awsProject

## Descrição
API FastAPI simulando autenticação AWS Cognito (JWT), provider LLM mock e pipeline RAG básico.

## Estrutura
- `src/` — código principal
- `infra/` — JWKS e chaves de teste
- `tests/` — testes automatizados

## Como rodar localmente
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\Activate.ps1  # Windows PowerShell
pip install -r requirements.txt
uvicorn src.main:app --reload
```
## Gerar tokens JWT de teste via API
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
  -d '{"prompt":"Como funciona RAG?"}'
```

## Alternativa: Gerar token via script
Se preferir, você também pode gerar um token usando o script
```bash
python scripts/generate_token.py > token.txt
```