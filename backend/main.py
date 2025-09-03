# backend/main.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Dev CORS (safe because FE/BE are same machine in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Odyssey ROV Backend is running"}

@app.get("/healthz")
def health():
    return {"status": "ok"}

@app.websocket("/ws")
async def ws(ws: WebSocket):
    await ws.accept()
    await ws.send_text("connected")
    try:
        while True:
            msg = await ws.receive_text()
            await ws.send_text(f"echo: {msg}")
    except Exception:
        # client disconnected or error; close gracefully
        pass
    finally:
        await ws.close()