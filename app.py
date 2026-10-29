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
                {"role": "system", "content": "You are Rivo, a helpful WhatsApp assistant. Reply friendly and short. If user speaks Bangla, reply in Bangla."},
                {"role": "user", "content": user_message}
            ]
        }
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return "Sorry, I'm thinking slow. Try again?"

@app.route("/", methods=["GET"])
def home():
    return "Rivo Bot Running", 200

@app.route("/webhook", methods=["GET"])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "fail", 403

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print(data)
    try:
        if data.get('object') == 'whatsapp_business_account':
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    msgs = change.get('value', {}).get('messages', [])
                    if msgs and msgs[0]['type'] == 'text':
                        from_num = msgs[0]['from']
                        text = msgs[0]['text']['body']
                        ai_reply = get_ai_reply(text)
                        # Send reply
                        url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
                        headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
                        payload = {"messaging_product": "whatsapp", "to": from_num, "type": "text", "text": {"body": ai_reply}}
                        requests.post(url, json=payload, headers=headers)
    except Exception as e:
        print(e)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
