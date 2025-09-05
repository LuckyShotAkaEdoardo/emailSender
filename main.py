import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import resend

load_dotenv()
resend.api_key = os.getenv("RESEND_API_KEY")

EMAIL_TO = os.getenv("EMAIL_TO")
EMAIL_FROM = os.getenv("EMAIL_FROM") or "onboarding@resend.dev"  # fallback sicuro

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod metti il tuo dominio
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/send-email")
async def send_email(request: Request):
    if not resend.api_key:
        raise HTTPException(status_code=500, detail="Missing RESEND_API_KEY")

    data = await request.json()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    company = (data.get("company") or "").strip()
    site = (data.get("site") or "").strip()
    # honeypot opzionale
    hp = (data.get("hp") or "").strip()
    if hp:
        return {"ok": True, "skipped": True}  # bot ignorato

    if not name or not email or not message:
        raise HTTPException(status_code=422, detail="Missing fields")

    try:
        payload = {
            "from": EMAIL_FROM,            # usa onboarding@resend.dev se non hai dominio verificato
            "to": EMAIL_TO or email,       # opz.: invia a te; in fallback manda all’utente per test
            "subject": f"Nuovo messaggio dal portfolio: {name}",
            "reply_to": email,
            "text": f"Nome: {name}\nEmail: {email}\nAzienda: {company}\nSito: {site}\n\nMessaggio:\n{message}\n",
            "html": f"""
                <h2>Nuovo messaggio dal portfolio</h2>
                <p><b>Nome:</b> {name}</p>
                <p><b>Email:</b> {email}</p>
                {f"<p><b>Azienda:</b> {company}</p>" if company else ""}
                {f"<p><b>Sito:</b> {site}</p>" if site else ""}
                <p><b>Messaggio:</b><br/>{message.replace("\n","<br/>")}</p>
            """,
        }

        resp = resend.Emails.send(payload)  # SDK Resend
        # DEBUG: stampa su Render logs
        print("RESEND RESPONSE:", resp)

        # Alcune versioni del SDK tornano dict con 'id'; se fallisce, può esserci 'error'
        if not resp or not isinstance(resp, dict) or not resp.get("id"):
            # forza errore per non rispondere 200
            raise RuntimeError(f"Resend failed: {resp}")

        return {"ok": True, "id": resp["id"]}
    except Exception as e:
        # vedi dettagli nei log di Render
        print("RESEND ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")
