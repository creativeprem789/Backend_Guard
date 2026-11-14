import time

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# SEC-001: Hardcoded secret key
JWT_SECRET = "supersecretsecretkey12345678"

# CONF-002: Production debug mode explicitly True
app = FastAPI(debug=True)

# SEC-004: Insecure CORS with wildcard and credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Mock database client
class FakeDb:
    def execute(self, query):
        pass

    def get(self, user_id):
        return {"id": user_id}


db = FakeDb()


# PY-ASYNC-001 & SEC-002 & FASTAPI-001:
@app.get("/users/{user_id}")
async def get_user(user_id: str):
    # Synchronous blocking call inside async
    time.sleep(2)

    # SQL injection via f-string directly in route
    query = f"SELECT * FROM users WHERE id = '{user_id}'"
    db.execute(query)

    try:
        # DB-001: N+1 query in loop
        for item in [1, 2, 3]:
            db.get(item)
    except Exception:
        # ERR-001: Silent exception swallowing
        pass

    return {"user_id": user_id}
