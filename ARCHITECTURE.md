## DynamoDB — Modelagem single-table

### Tabela: `PromptHistory`
**PK**: `userId` (string) — ID do usuário  
**SK**: `ts#<timestamp>` (string) — ordena prompts por data

### Atributos adicionais
- `prompt` (string)
- `response` (string)
- `sourceDocs` (lista) — documentos usados no contexto RAG

### GSI1: `prompt-index`
- **PK**: `prompt`
- **SK**: `userId`
- Uso: buscar prompts iguais feitos por diferentes usuários.

---

## Exemplo de item
```json
{
  "userId": "user123",
  "SK": "ts#2025-08-15T15:30:00Z",
  "prompt": "Como funciona RAG?",
  "response": "Resposta simulada...",
  "sourceDocs": ["doc1", "doc2"]
}
```

## Fluxo de acesso
1. Salvar histórico — após gerar resposta no /v1/generate, inserir item na tabela.
2. Recuperar histórico por usuário — Query PK = userId ordenando por SK DESC.
3. Buscar por prompt — usar GSI1 para filtrar todos os usuários que fizeram a mesma pergunta.

## Arquitetura geral
- FastAPI recebe request
- JWT Middleware valida e extrai claims
- Endpoint /v1/auth/login gera JWT mock para testes
- RAG Pipeline busca contexto em retrive_context
- DynamoDB armazena histórico de interações (futuro)
- LLM Provider gera resposta (mock ou real)