import re

def sanitize_prompt_for_logging(prompt: str, max_len: int = 200) -> str:
    """
    Reduz e remove padrões óbvios de PII.
    Essa sanitização é simplificada apenas para ambiente de dev/test
    """

    # remove emails
    s = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED_EMAIL]", prompt)
    # remove long hex / token-like strings (ex.: AWS keys, token JWT longos)
    s = re.sub(r"\b[0-9a-fA-F]{20,}\b", "[REDACTED_TOKEN]", s)

    if len(s) > max_len:
        s = s[:max_len] + "...[truncated]"

    return s