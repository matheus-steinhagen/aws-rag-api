# --------------------------------------------------
# src/utils/idempotency.py
# --------------------------------------------------
# Store simples em memória para suportar Idempotency-Key
# - É um cabeçalho enviado pelo clente para garantir que,
# mesmo se a mesma requisição for repetida (ex. timeout, retry),
# o servidor só processe UMA VEZ
# - Muito usado em pagamentos, criação de recursos, APIs críticas
#
# Como funciona
# - Mantemos um dicionário em memória que guarda
#   { chave: (timestamp, bodyhash, data) }
# - TTL: cada entrada expira após x segundos → evita crescer para sempre
# - body_hash: impede reuso da mesma chave com payload diferentes (409)
# - locks: evitam corrida (duas requisições com a mesm chave ao mesmo tempo)
#
# Em termos de aprendizado
# - Idempotência em APIs: como evitar duplicidade de processamento
# - Mostra o uso de TTL, hash de corpo e asyncio.Lock
# - Segurança e consistência ao repetir chamadas após timeout
# - Demonstra uma prática muito comum em APIs de produção

import time
import json
import hashlib
import asyncio
from typing import Any, Dict, Optional, Tuple

class InMemoryIdempotencyStore:
    """
    Implementação simples de um cacho em memória para gerenciar Idempotency-Key
    Útil para garantir que requisiões repetidas não causem duplicidade de efeitos
    """
    def __init__(self, ttl_seconds: int = 600):
        """
        ttl_seconds: tempo de vida (em segundos) de cada chave
        - Ex.: se ttl=600, após 10 minutos a chave expira e pode ser reutilizada
        """
        self.ttl = ttl_seconds
        
        # Dicionário principal
        # key -> (timestamp, body_hash, data)
        #   timestamp: quando a entrada foi criada
        #   body_hash: hash do corpo da requisição (para detectar conflitos)
        #   data: a resposta já processada (para replay)
        self._store: Dict[str, Tuple[float, str, Dict[str, Any]]] = {}

        # Dicionário de locks por chave
        # - evita condição de corrida quando duas requisições chegam ao mesmo tempo
        # - exemplo: cliente dispara 2x a mesma request em paralelo
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # --------------------------------------------------
        # Métodos auxiliares privados
        # --------------------------------------------------

    def _now(self) -> float:
        """
        Retorna o timestamp atual (epoch time - em segundos)
        """
        return time.time()
    
    def _hash_body(self, body: Any) -> str:
        """
        Calcula hash SHA-256 do corpo da requisição
        - O json.dumps com sort_keys=True garante que a ordem das chaves
            não afete o hash (consistência determinística)
        - Isso garante que o mesmo payload gere sempre o mesmo hash
        """
        # hash determinístico do corpo (ordena chaves para estabilidade)
        raw = json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def acquire_lock(self, key:str) -> asyncio.Lock:
        """
        Retorna um asyncio.Lock para a chave
        - Se não existir, cria um novo lock
        - Faz lock.adquire() → só uma coroutine pode prosseguir por vez
        - Isso previne que duas requisições emultâneas processe a mesma chave
        """
        lock = self._locks.get(key)
        if not lock:
            lock = asyncio.Lock()
            self._locks[key] = lock
        await lock.acquire()
        return lock
    
    def body_hash(self, body: Any) -> str:
        """
        Wrapper público para gerar hash de um corpo
        Usado no main.py para comparar se um Idempotency-Key
        está sendo reutilizado com corpo diferente (→ erro 409)
        """
        return self._hash_body(body)
    
    def get_entry(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Retorna a entrada armazenada para uma chave, se existir e não tiver expirado
        Se a entrada expirou, ela é removida e retorna None
        """
        entry = self._store.get(key)
        if not entry:
            return None
        ts, body_hash, data = entry
        if self._now() - ts > self.ttl:
            #expirou → limpa
            del self._store[key]
            return None
        return {
            "ts": ts,
            "body_hash": body_hash,
            "data": data
        }
    
    def put(self, key: str, body: Any, data: Dict[str, Any]) -> None:
        """
        Adiciona ou substitui uma entrada no store
        - Guarda o timestamp atual
        - Guarda o hash do corpo
        - Garda a resposta (data)
        """
        self._store[key] = (self._now(), self._hash_body(body), data)