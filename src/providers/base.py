# --------------------------------------------------
# src/providers/base.py
# --------------------------------------------------
# Define a interface (contrato) que todos os provides devem seguir
#
# Isso conecta com boas práticas de design (SOLID, especialmente "L" de Liskov)
# Assim, qualquer implementação pode substituir a outra sem quebrar o código
#
# Em termos de aprendizado
# - Desenvolve a maturidade de design e escalabilidade
# --------------------------------------------------

from abc import ABC, abstractmethod

class LLMProvider(ABC):
    """
    Interface base para qualquer provedor LLM.
    - Todos os providers (mock, OpenAI, Bedrock) devem herdar daqui
    - Isso obrigad a implementação de generate_text (prompt)

    Vantagens
    - O código não depende de detalhe da implementação
    - Podemos trocar MockProvider por BedrockProvider facilmente
    """

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Gera texto a partir de um prompt
        - prompt: string com a entrada do usuário
        - retorno: string gerada pelo modelo

        Em produção, aqui chamaríamos a API externa do LLM
        """
        raise NotImplementedError # Explicitamos que deve ser implementado