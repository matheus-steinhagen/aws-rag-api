## DynamoDB — Modelagem single-table

### Tabela: `PromptHistory`
**PK**: `user_id` (string) — ID do usuário
**SK**: `request_id` (string) — identificador único da requisição

### Atributos adicionais
- `prompt` (string)
- `response` (string)

### GSI1: `prompt-index`
- **PK**: `prompt`
- **SK**: `userId`
- Uso: buscar prompts iguais feitos por diferentes usuários.

---

## Exemplo de item
```json
{
  "userId": "user123",
  "SK": "req-12345",
  "prompt": "Como funciona RAG?",
  "response": "Resposta simulada...",
  "sourceDocs": ["doc1", "doc2"]
}
```

## Fluxo de acesso
1. Salvar histórico — após gerar resposta no /v1/generate, inserir item na tabela.
2. Recuperar histórico — Query PK = user_id, retornando todos os requests feitos.
3. Recuperar item específico — GetItem (user_id + request_id).

## Arquitetura geral
- FastAPI recebe request
- JWT Middleware valida e extrai claims
- Endpoint /v1/auth/login gera JWT mock para testes
- RAG Pipeline busca contexto em `retrive_context`
- DynamoDB (via moto em `dev`, real em prod) armazena histórico.
- LLM Provider gera resposta mockada.
