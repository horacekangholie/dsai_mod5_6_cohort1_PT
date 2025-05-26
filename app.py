from flask import Flask,request,render_template
import google.generativeai as genai
from openai import OpenAI
from markdown2 import Markdown
import os
from dotenv import load_dotenv
import sqlite3
import datetime
import requests

# Load environement variables from .env into os.environ
load_dotenv()

# Fetch API keys
gemini_key = os.getenv("GEMINI_KEY")
openai_key = os.getenv("OPENAI_KEY")
telegram_gemini_token = os.getenv("GEMINI_TELEGRAM_TOKEN")

# Configure Gemini
genai.configure(api_key=gemini_key)

# Configure OpenAI
client = OpenAI(api_key=openai_key)

# genmini_api_key = os.getenv("GEMINI_KEY")
# genmini_client = genai1.Client(api_key=genmini_api_key)
# genmini_model = "gemini-2.0-flash"

# Configure Gemini model
# model = genai.GenerativeModel("gemini-2.0-flash")
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

# Flask
app = Flask(__name__)


# Index
@app.route("/",methods=["GET","POST"])
def index():
    return(render_template("index.html"))


# Gemini
@app.route("/gemini",methods=["GET","POST"])
def gemini():
    return(render_template("gemini.html"))

@app.route("/gemini_reply",methods=["GET","POST"])
def gemini_reply():
    q = request.form.get("q")
    print(q)
    r = model.generate_content(q)
    r = r.text
    return(render_template("gemini_reply.html", r=r))


# OpenAI
@app.route("/openai",methods=["GET","POST"])
def openai():
    return(render_template("openai.html"))

@app.route("/openai_reply",methods=["GET","POST"])
def openai_reply():
    q = request.form.get("q")
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[{"role": "user", "content": q}]
    )
    r = response.choices[0].message.content

    markdowner = Markdown()
    formatted_response = markdowner.convert(r)
    return(render_template("openai_reply.html", r=formatted_response))


# Transfer Money
@app.route("/paynow",methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))


# Telegram
# Telegram: configure webhook
@app.route("/start_telegram", methods=["GET", "POST"])
def start_telegram():
    # Phase 1: show the “Start Telegram” button
    if request.method == "GET":
        return render_template("telegram.html")

    # Phase 2: actually register the webhook
    domain_url = os.getenv("WEBHOOK_URL")
    token = telegram_gemini_token

    if not domain_url:
        status = "🚨 Error: WEBHOOK_URL not set in environment"
        return render_template("start_telegram.html", status=status)

    # 1) Delete any existing webhook
    delete_url = f"https://api.telegram.org/bot{token}/deleteWebhook"
    resp_del = requests.post(delete_url, json={"drop_pending_updates": True})

    # 2) Register your new webhook
    set_url = f"https://api.telegram.org/bot{token}/setWebhook"
    resp_set = requests.post(set_url, json={
        "url": f"{domain_url}/telegram",
        "drop_pending_updates": True
    })

    if resp_set.status_code == 200:
        status = "✅ Telegram bot is running! Send your bot a message now."
    else:
        status = (
            f"❌ Failed to set webhook: "
            f"{resp_set.status_code} {resp_set.text}"
        )

    return render_template("start_telegram.html", status=status)


# Telegram: receive updates
@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    update = request.get_json(force=True)

    # Only proceed if there's a message with text
    if update.get("message", {}).get("text"):
        chat_id = update["message"]["chat"]["id"]
        text    = update["message"]["text"].strip()

        if text == "/start":
            r_text = "Welcome to the Financial Advisor Bot! Ask me any finance question."
        else:
            system_prompt = (
                "You are a financial expert. Answer ONLY questions related to "
                "finance, economics, investing, and financial markets. "
                "If the question is not related, say you can’t answer it."
            )
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            out = model.generate_content(prompt)
            r_text = out.text

        # Send the response back
        send_url = f"https://api.telegram.org/bot{telegram_gemini_token}/sendMessage"
        requests.post(send_url, data={
            "chat_id": chat_id,
            "text":    r_text
        })

    # Telegram requires a 200 OK within a short timeout
    return "OK", 200


# Prediction
@app.route("/prediction",methods=["GET","POST"])
def prediction():
    return(render_template("prediction.html"))

@app.route("/prediction_reply",methods=["GET","POST"])
def prediction_reply():
    q = float(request.form.get("q"))
    print(q)
    return(render_template("prediction_reply.html", r=90.2 + (-50.6*q)))


# Working with databse
@app.route("/main",methods=["GET","POST"])
def main():
    # Get the user input
    q = request.form.get("q", "").strip()  # default to "" and strip whitespace
    t = datetime.datetime.now()

    if q:
        # Insert record to table - users
        conn = sqlite3.connect('user.db')
        c = conn.cursor()
        c.execute("INSERT INTO users(name, timestamp) VALUES(?, ?)", (q, t))
        conn.commit()
        conn.close()
    else:
        pass
   
    return(render_template("main.html"))

@app.route("/user_log",methods=["GET","POST"])
def user_log():
    # Recursively display record from table - users
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users")

    r = c.fetchall()
    
    c.close()
    conn.close()
    return(render_template("user_log.html", usr=r))


@app.route("/delete_log",methods=["GET","POST"])
def delete_log():
    # Delete records from table - users
    conn = sqlite3.connect("user.db")
    c = conn.cursor()
    c.execute("DELETE FROM users")
    conn.commit()
    c.close()
    conn.close()
    return(render_template("delete_log.html"))


# Logout
@app.route("/logout",methods=["GET","POST"])
def logout():
    global first_time
    first_time = 1
    return(render_template("index.html"))


# Main
if __name__ == "__main__":
    app.run()
    # app.run(host="0.0.0.0", port=8080, debug=True) # debug=True turns on the reloader
    