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
- Endpoint `/v1/generate` protegido por JWT, respondendo via MockProvider e contexto de mock de RAG
- Endpoint /v1/auth/login para gerar jwt de teste
- FUnção get_user_roles para mapear claims → roles
- Dockerfile e .gitignore criados

## Próximos passos (Dia 1 pendentes)
1. Implementar persistência real no DynamoDB
2. Criar testes unitários para autenticação e geração
3. Implementar middleware de idempotência
4. Adicionar logs e métricas
5. Pipeline RAG com embeddings reais

## Entregáveis
- Código no GitHub.
- Documentação (`PROJECT_PLAN.md`, `README.md`, `ARCHITECTURE.md`).