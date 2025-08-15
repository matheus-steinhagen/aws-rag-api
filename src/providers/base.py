# src/providers/base.py

# Interface base para qualquer provedor LLM
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Interface base para qualquer provedor LLM.
    Documentação rápida: qualquer implementador deve sobrescrever generate_text.
    """

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Gera texto a partir de um prompt
        - prompt: string com a entrada do usuário
        - retorno: string gerada pelo modelo
        """
        raise NotImplementedError # Explicitamos que deve ser implementado