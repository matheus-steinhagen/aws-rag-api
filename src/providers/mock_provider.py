# --------------------------------------------------
# src/providers/mock_provider.py
# --------------------------------------------------
# Este arquivo implementa um "provedor falso" de LLM
# O objetivo é simular respostas de um modelo de linguagem
# (como GPT-4 ou AWS Bedrock) sem precisar gastar dinheiro
# e sem depender de conexões externas
#
# Em termos de aprendizado
# - Como escolher quando usar modelos caros ou baratos
# - Permite treinar idempotência, retry, circuit breaker (sem custo real)
# - Serve como 'mock' para testes automatizados → TDD/CI

import random
from .base import LLMProvider

# --------------------------------------------------
# MockProvider
# --------------------------------------------------
# Essa classe herda da interface LLMProvider (definida em base.py)
# Isso garante que qualquer provider real (OpenAI, Bedrock) siga o mesmo contrato
# Ou Seja: todos devem implementar 'generate_text'
#
# Em termos de aprendizado
# - Como aplicar o uso de abstração (programar contra interface, não implementação)
# - COmo manter código desacoplado para trocar providers facilmente
class MockProvider(LLMProvider):
    """
    MockProvider implementa generate_text de forma assíncrona,
    simulando respostas de um LLM real
    
    Exemplo prático
    - Usuário manda "O que é RAG?"
    - Mock responde com uma frase genérica, como se fosse o modelo.

    Isso é ótimo para:
    - Teste unitário (não precisamos de internet nem credenciais)
    - Demonstrações (sem custo de API)
    """

    async def generate_text(self, prompt: str) -> str:
        """
        Gera uma resposta simulada a partir de um prompt
        EM produção, aqui chamaríamos o LLM real (ex. Bedrock, OpenAI)
        """
        respostas = [
            f"Entendi que você quer saber sobre {prompt}",
            f"Posso explicar isso de forma simples: {prompt}",
            f"Aqui está uma resposta simulada para {prompt}",
            f"Simulação: {prompt} - resposta fictícia"
        ]
        # Escolhemos uma resposta aleatória → simula variação de modelos reais
        return random.choice(respostas)