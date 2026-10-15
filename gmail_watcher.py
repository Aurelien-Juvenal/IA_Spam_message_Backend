import imaplib
import email
from email.header import decode_header
import requests
import time

# --- CONFIGURATION ---
GMAIL_USER = "aurelienjuvenal@gmail.com"
GMAIL_APP_PASSWORD = "dglc gnzi oolu elul"  # Le mot de passe d'application à 16 caractères
API_URL = "http://127.0.0.1:8000/predict"   # Remplacez par votre URL Hugging Face en production

def clean_header(header_value):
    """Décode les en-têtes d'e-mail (sujet, expéditeur)."""
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    header_str = ""
    for bytes_or_str, encoding in decoded_list:
        if isinstance(bytes_or_str, bytes):
            header_str += bytes_or_str.decode(encoding or "utf-8", errors="ignore")
        else:
            header_str += bytes_or_str
    return header_str

def get_email_body(msg):
    """Extrait le contenu textuel d'un e-mail."""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return part.get_payload(decode=True).decode("utf-8", errors="ignore")
    else:
        return msg.get_payload(decode=True).decode("utf-8", errors="ignore")
    return ""
from datetime import datetime

def check_new_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        # Tentative de sélection du dossier INBOX standard
        status, _ = mail.select("INBOX")
        
        # Si INBOX échoue, essayer les dossiers de secours
        if status != 'OK':
            status, _ = mail.select('"[Gmail]/Tous les messages"')
        if status != 'OK':
            status, _ = mail.select('"[Gmail]/All Mail"')

        if status != 'OK':
            print("[ERREUR] Impossible de sélectionner un dossier Gmail valide.")
            mail.logout()
            return

        # Récupération des 5 derniers messages
        status, messages = mail.search(None, 'ALL')
        if status != 'OK' or not messages[0]:
            print("[LOG] Aucun message trouvé.")
            mail.logout()
            return

        email_ids = messages[0].split()[-5:]
        print(f"[LOG] Analyse des {len(email_ids)} derniers messages...")

        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    subject = clean_header(msg["Subject"])
                    sender = clean_header(msg["From"])
                    body = get_email_body(msg)
                    
                    full_text = f"Subject: {subject}\nFrom: {sender}\n\n{body}".strip()
                    if not body.strip():
                        full_text = f"Subject: {subject} From: {sender}"

                    response = requests.post(API_URL, json={"text": full_text})
                    
                    if response.status_code == 200:
                        res_data = response.json()
                        status_str = "🔴 SPAM" if res_data["is_spam"] else "🟢 SAFE"
                        print(f"\n----------------------------------------")
                        print(f"De       : {sender}")
                        print(f"Sujet    : {subject}")
                        print(f"Verdict  : {status_str} (Confiance: {res_data['confidence'] * 100:.1f}%)")
                        print(f"----------------------------------------")
                    else:
                        print(f"[ERREUR API] Code {response.status_code}")

        mail.logout()

    except Exception as e:
        print(f"[ERREUR] : {str(e)}")

if __name__ == "__main__":
    print("=== Démarrage de la surveillance Gmail ===")
    # Boucle de vérification toutes les 30 secondes
    while True:
        check_new_emails()
        time.sleep(30)