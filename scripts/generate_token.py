#scripts/generate_token.py

import jwt
import time
from pathlib import Path

PRIVATE = Path("private.pem").read_text()
payload = {
    "sub": "user123",
    "email": "candidate@example.com",
    "iat": int(time.time()),
    "exp": int(time.time()) + 3600,
    "custom:roles": ["user"]
}

#incluir header com kid igual ao jwks.json
token = jwt.encode(payload, PRIVATE, algorithm="RS256", headers={"kid": "test-key-1"})
print(token)