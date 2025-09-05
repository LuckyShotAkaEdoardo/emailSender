import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import resend

# carica variabili ambiente
load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

app = FastAPI()

# Abilita CORS per collegarti dal frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # in prod metti solo il tuo dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/send-email")
async def send_email(request: Request):
    data = await request.json()
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not name or not email or not message:
        return {"error": "Missing fields"}

    try:
        r = resend.Emails.send({
            "from": os.getenv("EMAIL_FROM"),
            "to": os.getenv("EMAIL_TO"),
            "subject": f"Nuovo messaggio dal portfolio: {name}",
            "reply_to": email,
            "html": f"""
                <h2>Nuovo messaggio dal portfolio</h2>
                <p><b>Nome:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                <p><b>Messaggio:</b><br/>{message.replace("\n","<br/>")}</p>
            """
        })
        return {"ok": True, "id": r["id"]}
    except Exception as e:
        return {"error": str(e)}
