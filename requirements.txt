from flask import Flask, request
import requests
import os

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "rivo12345")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

def get_ai_reply(user_message):
    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are Rivo, a helpful WhatsApp assistant for rivoSIM in Bangladesh. Reply friendly and short. If user speaks Bangla, reply in Bangla."},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.7
        }
        r = requests.post(url, json=payload, headers=headers, timeout=25)
        data = r.json()
        print(f"GROQ RESPONSE: {data}")
        return data['choices'][0]['message']['content']
    except Exception as e:
        print(f"GROQ ERROR: {e}")
        return "Hi! I am Rivo from rivoSIM. How can I help you?"

@app.route("/", methods=["GET"])
def home():
    return "Rivo Bot Running - Permanent Token Version", 200

@app.route("/webhook", methods=["GET"])
def verify():
    print(f"VERIFY ATTEMPT: {request.args}")
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        print("VERIFY SUCCESS")
        return request.args.get("hub.challenge")
    print("VERIFY FAILED")
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(f"INCOMING WEBHOOK: {data}")
    try:
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    if messages:
                        msg = messages[0]
                        if msg.get('type') == 'text':
                            from_num = msg['from']
                            text = msg['text']['body']
                            print(f"MESSAGE FROM {from_num}: {text}")
                            
                            ai_reply = get_ai_reply(text)
                            print(f"AI REPLY: {ai_reply}")
                            
                            url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
                            headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
                            payload = {
                                "messaging_product": "whatsapp",
                                "to": from_num,
                                "type": "text",
                                "text": {"body": ai_reply}
                            }
                            resp = requests.post(url, json=payload, headers=headers)
                            print(f"WHATSAPP SEND STATUS: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"WEBHOOK ERROR: {e}")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
