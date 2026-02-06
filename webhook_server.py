#!/usr/bin/env python3
"""
Webhook server for n8n integration.
Exposes an endpoint that triggers the transcript pipeline.
"""

import os
import subprocess
import threading
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Secret token for basic auth (set in .env)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "change-me-in-production")

def run_pipeline(page_id=None, url=None):
    """Run the pipeline in a background thread"""
    try:
        if page_id and url:
            # Process specific entry
            result = subprocess.run(
                ["python", "process_single.py", page_id, url],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
        else:
            # Process all pending entries
            result = subprocess.run(
                ["python", "process_all.py"],
                capture_output=True,
                text=True,
                timeout=600,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )

        print(f"Pipeline completed. Return code: {result.returncode}")
        if result.stdout:
            print(f"Output: {result.stdout[:500]}")
        if result.stderr:
            print(f"Errors: {result.stderr[:500]}")

    except Exception as e:
        print(f"Pipeline error: {e}")

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok"})

@app.route("/webhook/process", methods=["POST"])
def process_webhook():
    """
    Webhook endpoint for n8n.

    Optional JSON body:
    {
        "secret": "your-webhook-secret",
        "page_id": "notion-page-id",
        "url": "content-url"
    }
    """
    data = request.get_json() or {}

    # Verify secret
    secret = data.get("secret") or request.headers.get("X-Webhook-Secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # Get optional parameters
    page_id = data.get("page_id")
    url = data.get("url")

    # Run pipeline in background thread (don't block the response)
    thread = threading.Thread(target=run_pipeline, args=(page_id, url))
    thread.start()

    return jsonify({
        "status": "processing",
        "message": "Pipeline started in background"
    })

@app.route("/webhook/process-all", methods=["POST"])
def process_all_webhook():
    """Process all pending entries"""
    data = request.get_json() or {}

    secret = data.get("secret") or request.headers.get("X-Webhook-Secret")
    if secret != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    thread = threading.Thread(target=run_pipeline)
    thread.start()

    return jsonify({
        "status": "processing",
        "message": "Processing all pending entries"
    })

if __name__ == "__main__":
    print("Starting webhook server on port 5050...")
    print(f"Health check: http://localhost:5050/health")
    print(f"Webhook endpoint: http://localhost:5050/webhook/process")
    app.run(host="0.0.0.0", port=5050, debug=False)
