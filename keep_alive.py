from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Join the discord: https://discord.gg/TqVH6NBwS3"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()
