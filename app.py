"""
ClaimLens - Claim triage for Indonesian social media posts.

Paste a claim, ClaimLens retrieves the closest verified fact-check
from its corpus and returns a grounded verdict with the source:
SESUAI (matches a verified true claim), TIDAK SESUAI (matches a
debunked claim), MERAGUKAN (partial / weak match), or
TIDAK DITEMUKAN (no verified reference close enough).

Built during HackGlobal 2026 (Polaris School of Technology x Vultr),
Track 4: Civic and real-world impact.
"""

import json
import math
import os
import re
from collections import Counter

from flask import Flask, jsonify, render_template, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "claims.json")

STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "pada", "adalah", "akan", "tidak", "ada", "oleh", "sebagai", "dalam",
    "atau", "juga", "sudah", "karena", "bisa", "dapat", "telah", "para",
    "saat", "agar", "bagi", "lebih", "sangat", "sebuah", "bahwa", "mereka",
    "kita", "kami", "anda", "dia", "ia", "apa", "apakah", "benarkah",
    "katanya", "viral", "beredar", "pesan", "berantai", "tolong", "share",
    "sebarkan", "info", "informasi", "menurut", "tahun", "orang", "jadi",
    "harus", "kalau", "jika", "maka", "namun", "tetapi", "tapi", "lagi",
    "semua", "setiap", "antara", "tentang", "kepada", "secara", "usai",
}

TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text):
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS and len(t) > 2]


class TfidfIndex:
    """Minimal TF-IDF + cosine similarity index, pure Python."""

    def __init__(self, docs_tokens):
        self.n = len(docs_tokens)
        df = Counter()
        for tokens in docs_tokens:
            for term in set(tokens):
                df[term] += 1
        self.idf = {
            term: math.log((self.n + 1) / (count + 1)) + 1.0
            for term, count in df.items()
        }
        self.vectors = [self._vectorize(t) for t in docs_tokens]

    def _vectorize(self, tokens):
        tf = Counter(tokens)
        vec = {}
        for term, count in tf.items():
            if term in self.idf:
                vec[term] = (1.0 + math.log(count)) * self.idf[term]
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {term: v / norm for term, v in vec.items()}

    def search(self, query_text, top_k=3):
        qvec = self._vectorize(tokenize(query_text))
        scored = []
        for idx, dvec in enumerate(self.vectors):
            score = sum(qvec[t] * dvec.get(t, 0.0) for t in qvec)
            if score > 0:
                scored.append((idx, round(score, 4)))
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:top_k]


def load_corpus():
    with open(DATA_PATH, encoding="utf-8") as fh:
        entries = json.load(fh)
    docs = [tokenize(e["claim"] + " " + e.get("keywords", "")) for e in entries]
    return entries, TfidfIndex(docs)


ENTRIES, INDEX = load_corpus()

# Similarity thresholds for verdict mapping.
STRONG_MATCH = 0.32
WEAK_MATCH = 0.15

app = Flask(__name__)


def verdict_for(entry, score):
    if score >= STRONG_MATCH:
        if entry["label"] == "VALID":
            return "SESUAI"
        if entry["label"] == "HOAKS":
            return "TIDAK SESUAI"
        return "MERAGUKAN"
    if score >= WEAK_MATCH:
        return "MERAGUKAN"
    return "TIDAK DITEMUKAN"


@app.get("/")
def home():
    return render_template("index.html", corpus_size=len(ENTRIES))


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "corpus_size": len(ENTRIES)})


@app.post("/api/check")
def check():
    payload = request.get_json(silent=True) or {}
    claim = (payload.get("claim") or "").strip()
    if len(claim) < 8:
        return jsonify({"error": "Claim too short, at least 8 characters."}), 400

    results = INDEX.search(claim, top_k=3)
    if not results:
        return jsonify({
            "query": claim,
            "verdict": "TIDAK DITEMUKAN",
            "score": 0.0,
            "match": None,
            "references": [],
            "explanation": "No fact-check reference in the ClaimLens corpus is "
                           "close enough to this claim yet.",
        })

    best_idx, best_score = results[0]
    best = ENTRIES[best_idx]
    verdict = verdict_for(best, best_score)

    references = []
    for idx, score in results:
        entry = ENTRIES[idx]
        references.append({
            "claim": entry["claim"],
            "label": entry["label"],
            "source": entry["source"],
            "source_url": entry["source_url"],
            "score": score,
        })

    if verdict == "SESUAI":
        explanation = ("This claim closely matches a verified fact: "
                       + best["summary_en"])
    elif verdict == "TIDAK SESUAI":
        explanation = ("This claim closely matches a claim already debunked "
                       "by fact-checkers: " + best["summary_en"])
    elif verdict == "MERAGUKAN":
        explanation = ("There is some similarity to a verified reference, "
                       "but not enough for a firm conclusion. Closest "
                       "reference: " + best["summary_en"])
    else:
        explanation = ("Similarity to the corpus is too low, so this claim "
                       "is unverified for now. Treat it as unclear and check "
                       "the official source.")

    return jsonify({
        "query": claim,
        "verdict": verdict,
        "score": best_score,
        "match": {
            "claim": best["claim"],
            "label": best["label"],
            "source": best["source"],
            "source_url": best["source_url"],
            "summary": best["summary"],
        } if verdict != "TIDAK DITEMUKAN" else None,
        "references": references,
        "explanation": explanation,
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
