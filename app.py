from flask import Flask,request,render_template
import google.generativeai as genai
from openai import OpenAI
from markdown2 import Markdown
import os
from dotenv import load_dotenv
import sqlite3
import datetime

# Load environement variables from .env into os.environ
load_dotenv()

# Fetch API keys
gemini_key = os.getenv("GEMINI_KEY")
openai_key = os.getenv("OPENAI_KEY")

# Configure Gemini
genai.configure(api_key=gemini_key)

# Configure OpenAI
client = OpenAI(api_key=openai_key)

# Configure Gemini model
# model = genai.GenerativeModel("gemini-2.0-flash")
model = genai.GenerativeModel("gemini-2.5-flash-preview-04-17")

# Flask
app = Flask(__name__)


# Gemini
@app.route("/",methods=["GET","POST"])
def index():
    return(render_template("index.html"))

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


@app.route("/paynow",methods=["GET","POST"])
def paynow():
    return(render_template("paynow.html"))



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

@app.route("/logout",methods=["GET","POST"])
def logout():
    global first_time
    first_time = 1
    return(render_template("index.html"))



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


if __name__ == "__main__":
    app.run()
    # app.run(host="0.0.0.0", port=8080, debug=True) # debug=True turns on the reloader
    