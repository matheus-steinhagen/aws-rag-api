# --------------------------------------------------
# src/utils/rety.py
# --------------------------------------------------
# Retry assíncrono com backoff exponencial + jitter
#
# Em termos de aprendizado
# - Resiliência frente a falhas transitórias de serviços externos
# - Evitar tempestades (thundering herd) com jitter aleatório

import asyncio
import random
from typing import Awaitable, Callable, Iterable, Tuple, Type

async def retry_async(
    func: Callable[[], Awaitable],
    *,
    attempts: int = 3,
    min_delay: float = 0.2,
    max_delay: float = 2.0,
    exceptions: Iterable[type[BaseException]] = (Exception,),
    jitter: bool = True
):
    last_exc = None
    for i in range(attempts):
        try:
            return await func()
        except exceptions as e:
            last_exc = e
            if i == attempts - 1:
                break
            delay = min(max_delay, min_delay * (2 ** i))
            if jitter:
                delay = delay * (0.5 + random.random()) # 0.5x..1.5x
            await asyncio.sleep(delay)
    raise last_exc