# --------------------------------------------------
# src/utils/circuit_breaker.py
# --------------------------------------------------
# Implementação simples do padrão "Circuit Braker"
#
# Estados
# - CLOSED: aceita requisições normalmente
# - OPEN: bloqueia requisições por um tempo (recovery_time)
# - HALF_OPEN: depoi do tempo de bloqueio, permite UMA tentativa
#   > Se sucesso → CLOSED
#   > Se falha → OPEN
#
# Em termos de aprendizado
# - Evita cascatas de erro em sistemas distribuidos
# - Dá tempo para serviços instaǘels se recuperarem
# - Muito usado em microserviços, APIs e chamadas externas (ex. LLMs, bancos, etc.)


import time
import asyncio

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_time: float = 10.0):
        """
        failure_threshold: número de falhas consecutivas para abrir o circuito
        recovery_time: tempo (segundos) que o circuito fica "aberto" antes de testar de novo
        """
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time

        # Estado inicial → aceita tudo
        self.state = "CLOSED"

        # Contador de falhas consecutivas
        self.fail_count = 0

        # Quando o circuito abriu (para saber se já passou recovery_time)
        self.opened_at = 0.0

        # Lock assíncrono → garante que várias coroutines não mudem o estado ao mesmo tempo
        self._lock = asyncio.Lock()

    # --------------------------------------------------
    # Consulta se pode processaR a requisição
    # --------------------------------------------------
    async def allow_request(self) -> bool:
        """
        Retorna TRUE se a requisição pode seguir, False se deve ser bloqueada
        - CLOSED: sempre True
        - OPEN: False, a menos que já tenha passado o recovery_time → vira HALF_OPEN
        - HALF_OPEN: True (permite uma tentativa de teste)
        """
        async with self._lock:
            if self.state == "OPEN":
                # Está bloqueado → verifica se já deu tempo para tentar de novo
                if time.time() - self.opened_at >= self.recovery_time:
                    self.state = "HALF_OPEN"
                    return True
                return False
            return True # CLOSED ou HALF_OPEN permitem tentativa

    # --------------------------------------------------
    # Atualiza estado em caso de sucesso
    # --------------------------------------------------
    async def on_success(self):
        """
        Chamado quando a requisição foi bem sucedida
        - Zera o contador de falhas
        - Fecha o circuito (volta para CLOSED)
        """
        async with self._lock:
            self.fail_count = 0
            self.state = "CLOSED"

    # --------------------------------------------------
    # Atualiza estado em caso de falha
    # --------------------------------------------------
    async def on_failure(self):
        """
        Chamado quando a requisição falhou
        - Se estava HALF_OPEN → volta a OPEN imediatamente
        - Se acumulou falhas >= threshold → abre o circuito (OPEN)
        """
        async with self._lock:
            self.fail_count += 1
            if self.state == "HALF_OPEN":
                # falou no teste -> volta a OPEN
                self.state = "OPEN"
                self.opened_at = time.time()
                return
            if self.fail_count >= self.failure_threshold:
                # Muitas falhas consecutivas → abre o circuito
                self.state = "OPEN"
                self.opened_at = time.time()