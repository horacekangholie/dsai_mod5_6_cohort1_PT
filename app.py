#gemini
from flask import Flask,request,render_template
import google.generativeai as genai
import os

# Configure Gemini
genai.configure(api_key=os.environ["gemini_key"])
# genai.configure(api_key="<INSERT_GEMINI_API_KEY>")
model = genai.GenerativeModel("gemini-2.0-flash")

# Flask
app = Flask(__name__)

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
    return(render_template("gemini_reply.html",r=r.text))

if __name__ == "__main__":
    app.run()