"""Influenza A protein interaction checker (Flask).

Run:  python app.py   ->  http://127.0.0.1:5001
"""
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from data_loader import INTERACTOME_NAME, RECORDS, RNP_ORDER, lookup, suggest

app = Flask(__name__)
SUMMARY_FILE = Path(__file__).parent / "results" / "analysis_summary.json"


@app.get("/")
def index():
    return render_template("index.html", rnps=RNP_ORDER, interactome=INTERACTOME_NAME, total=len(RECORDS))


@app.get("/api/lookup")
def api_lookup():
    return jsonify(lookup(request.args.get("protein", "")))


@app.get("/api/suggest")
def api_suggest():
    return jsonify(suggest(request.args.get("q", "")))


@app.get("/analysis")
def analysis():
    summary = json.loads(SUMMARY_FILE.read_text()) if SUMMARY_FILE.exists() else None
    return render_template("analysis.html", summary=summary)


if __name__ == "__main__":
    app.run(debug=True, port=5001)  # 5000 is taken by macOS AirPlay Receiver
