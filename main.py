# main.py (handler minimale e "a prova di bomba")
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import resend

resend.api_key = os.getenv("RESEND_API_KEY")
EMAIL_TO = os.getenv("EMAIL_TO")  # es: "tua.email@gmail.com"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in prod limita al tuo dominio FE
    allow_credentials=True,
    allow_methods=["POST", "OPTIONS", "GET"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"ok": True, "from": "onboarding@resend.dev", "to_set": bool(EMAIL_TO)}

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

    if hp:  # honeypot → ignora bot
        return {"ok": True, "skipped": True}

    if not name or not email or not message:
        raise HTTPException(status_code=422, detail="Missing fields")

    # Resend: to DEVE essere lista
    to_list = [EMAIL_TO] if EMAIL_TO else [email]

    try:
        resp = resend.Emails.send({
            "from": "onboarding@resend.dev",   # mittente di test ufficiale
            "to": to_list,                      # SEMPRE array
            "subject": f"Nuovo messaggio: {name}",
            "text": (
                f"Da: {name} <{email}>\n"
                f"Azienda: {company}\nSito: {site}\n\n"
                f"{message}\n"
            ),
        })
        print("RESEND RESPONSE:", resp)
        if not isinstance(resp, dict) or not resp.get("id"):
            raise RuntimeError(f"Resend failed: {resp}")
        return {"ok": True, "id": resp["id"]}

    except Exception as e:
        # stampa dettagli utili nei log Render
        print("RESEND ERROR:", repr(e), getattr(e, "__dict__", {}))
        raise HTTPException(status_code=500, detail=f"Email send failed: {e}")
