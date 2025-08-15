# src/providers/mock_provider.py

# Simulação simples de provedor LLM para desenvolvimento local
import random
from .base import LLMProvider

class MockProvider(LLMProvider):
    """
    MockProvider implementa generate_text de forma assíncrona,
    simulando respostas de um LLM real (bom para testes sem custo).
    """

    async def generate_text(self, prompt: str) -> str:
        # respostas simuladas — fácil de explicar em entrevistas
        respostas = [
            f"Entendi que você quer saber sobre {prompt}",
            f"Posso explicar isso de forma simples: {prompt}",
            f"Aqui está uma resposta simulada para {prompt}",
            f"Simulação: {prompt} - resposta fictícia"
        ]
        return random.choice(respostas)