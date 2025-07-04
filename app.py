# app.py
# Flask app to receive GitHub webhook events and save them to MongoDB

from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)

# ✅ Connect to your local MongoDB instance
client = MongoClient("mongodb://localhost:27017/")

# ✅ Select the database and collection
db = client['webhook_db']
collection = db['events']

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handles GitHub webhook POST requests"""
    event_type = request.headers.get('X-GitHub-Event')
    payload = request.json
    timestamp = datetime.utcnow().strftime("%d %B %Y - %I:%M %p UTC")
    author = payload.get("sender", {}).get("login", "Unknown")

    event_data = {
        "event_type": event_type,
        "timestamp": timestamp,
        "author": author
    }

    if event_type == "push":
        event_data["to_branch"] = payload.get("ref", "").split("/")[-1]

    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        event_data["from_branch"] = pr.get("head", {}).get("ref")
        event_data["to_branch"] = pr.get("base", {}).get("ref")

    if not collection.find_one({"event_type": event_type, "timestamp": timestamp}):
        collection.insert_one(event_data)
        print(f"✅ Saved to MongoDB: {event_data}")
    else:
        print("⚠️ Duplicate event skipped")

    return jsonify({"status": "stored"}), 200

@app.route('/events', methods=['GET'])
def show_events():
    """Returns last 10 events in JSON format"""
    events = list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(10))
    return jsonify(events)
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)


    