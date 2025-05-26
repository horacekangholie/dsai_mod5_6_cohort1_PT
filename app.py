from flask import Flask,request,render_template
import google.generativeai as genai1
from openai import OpenAI
from markdown2 import Markdown
import os
from dotenv import load_dotenv
import sqlite3
import datetime
import requests
from google import genai

# Load environement variables from .env into os.environ
load_dotenv()

# Fetch API keys
gemini_key = os.getenv("GEMINI_KEY")
openai_key = os.getenv("OPENAI_KEY")
telegram_gemini_token = os.getenv("GEMINI_TELEGRAM_TOKEN")

# Configure Gemini
# genai.configure(api_key=gemini_key)

# Configure OpenAI
client = OpenAI(api_key=openai_key)

genmini_api_key = os.getenv("GEMINI_KEY")
genmini_client = genai1.Client(api_key=genmini_api_key)
genmini_model = "gemini-2.0-flash"

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
@app.route("/start_telegram",methods=["GET","POST"])
def start_telegram():

    domain_url = os.getenv('WEBHOOK_URL')

    # The following line is used to delete the existing webhook URL for the Telegram bot
    delete_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/deleteWebhook"
    requests.post(delete_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    
    # Set the webhook URL for the Telegram bot
    set_webhook_url = f"https://api.telegram.org/bot{gemini_telegram_token}/setWebhook?url={domain_url}/telegram"
    webhook_response = requests.post(set_webhook_url, json={"url": domain_url, "drop_pending_updates": True})
    print('webhook:', webhook_response)
    if webhook_response.status_code == 200:
        # set status message
        status = "The telegram bot is running. Please check with the telegram bot. @gemini_tt_bot"
    else:
        status = "Failed to start the telegram bot. Please check the logs."
    
    return(render_template("telegram.html", status=status))


@app.route("/telegram",methods=["GET","POST"])
def telegram():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        # Extract the chat ID and message text from the update
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            r_text = "Welcome to the Gemini Telegram Bot! You can ask me any finance-related questions."
        else:
            # Process the message and generate a response
            system_prompt = "You are a financial expert.  Answer ONLY questions related to finance, economics, investing, and financial markets. If the question is not related to finance, state that you cannot answer it."
            prompt = f"{system_prompt}\n\nUser Query: {text}"
            r = genmini_client.models.generate_content(
                model=genmini_model,
                contents=prompt
            )
            r_text = r.text
        
        # Send the response back to the user
        send_message_url = f"https://api.telegram.org/bot{gemini_telegram_token}/sendMessage"
        requests.post(send_message_url, data={"chat_id": chat_id, "text": r_text})
    # Return a 200 OK response to Telegram
    # This is important to acknowledge the receipt of the message
    # and prevent Telegram from resending the message
    # if the server doesn't respond in time
    return('ok', 200)


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
    