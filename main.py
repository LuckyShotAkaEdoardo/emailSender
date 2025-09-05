import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import resend

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

EMAIL_TO = os.getenv("EMAIL_TO")                      # es. "tuamail@esempio.com"
EMAIL_FROM = os.getenv("EMAIL_FROM") or "onboarding@resend.dev"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod: metti il tuo dominio
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "service": "emailsender", "from": EMAIL_FROM, "to": EMAIL_TO is not None}

@app.post("/send-email")
async def send_email(request: Request):
    if not resend.api_key:
        raise HTTPException(status_code=500, detail="Missing RESEND_API_KEY")

    data = await request.json()
    name    = (data.get("name") or "").strip()
    email   = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    company = (data.get("company") or "").strip()
    site    = (data.get("site") or "").strip()
    hp      = (data.get("hp") or "").strip()

    if hp:
        return {"ok": True, "skipped": True}  # honeypot

    if not name or not email or not message:
        raise HTTPException(status_code=422, detail="Missing fields")

    # Resend vuole SEMPRE una lista per "to"
    to_list = [EMAIL_TO] if EMAIL_TO else [email]

    payload = {
        "from": EMAIL_FROM,
        "to": to_list,
        "subject": f"Nuovo messaggio dal portfolio: {name}",
        "reply_to": email,
        "text": (
            f"Nome: {name}\nEmail: {email}\nAzienda: {company}\nSito: {site}\n\n"
            f"Messaggio:\n{message}\n"
        ),
        "html": f"""
            <h2>Nuovo messaggio dal portfolio</h2>
            <p><b>Nome:</b> {name}</p>
            <p><b>Email:</b> {email}</p>
            {f"<p><b>Azienda:</b> {company}</p>" if company else ""}
            {f"<p><b>Sito:</b> {site}</p>" if site else ""}
            <p><b>Messaggio:</b><br/>{message.replace("\n","<br/>")}</p>
        """,
    }

    try:
        resp = resend.Emails.send(payload)  # sync call
        print("RESEND RESPONSE:", resp)

        # L’SDK valido torna un dict con "id"
        if not resp or not isinstance(resp, dict) or not resp.get("id"):
            raise RuntimeError(f"Resend failed: {resp}")

        return {"ok": True, "id": resp["id"]}
    except Exception as e:
        # Prova a tirar fuori più info dall’eccezione
        err_msg = getattr(e, "message", None) or str(e)
        err_dict = getattr(e, "__dict__", {})
        print("RESEND ERROR:", err_msg, err_dict)
        raise HTTPException(status_code=500, detail=f"Email send failed: {err_msg}")
