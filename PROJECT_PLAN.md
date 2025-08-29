## Visão geral
Projeto FastAPI com autenticação JWT (mock Cognito), provider LLM simulado e arquitetura preparada para RAG + DynamoDB.

## Objetivos
- Simular fluxo real de autenticação e autorização com JWKS local.
- Criar endpoints versionados e protegidos.
- Implementar provider LLM mock e pipeline RAG básico.
- Modelar DynamoDB para armazenar histórico de prompts.

## Status atual
- Estrutura de projeto criada (`src/`, `infra/`, `tests/`).
- Middleware JWT funcional com JWKS local.
- Endpoint `/v1/health` público.
- Endpoint `/v1/auth/login` para gerar JWT de teste.
- Endpoint `/v1/generate` protegido por JWT, respondendo via MockProvider e contexto RAG mockado.
- Endpoint `/v1/history` que consulta DynamoDB simulado via **moto**.
- Função `get_user_roles` para mapear claims → roles.
- Dockerfile e `.gitignore` criados.
- Testes automatizados para login, geração e histórico (✅ todos passando).

## Próximos passos
1. 📌 Migrar persistência de `moto` (mock) para DynamoDB real (produção).
2. 📌 Implementar middleware de idempotência.
3. 📌 Pipeline RAG com embeddings reais.
4. 📌 Aprimorar logging e métricas para observabilidade.

## Entregáveis
- Código no GitHub.
- Documentação (`PROJECT_PLAN.md`, `README.md`, `ARCHITECTURE.md`).
