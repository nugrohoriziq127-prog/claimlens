# ClaimLens

**Claim triage for Indonesian social media claims, grounded in verified fact-checks.**

Paste a claim from social media or a forwarded message. ClaimLens retrieves the
closest verified fact-check from its corpus and returns a verdict *with the
source*, so every answer can be checked by the user:

- **SESUAI** - the claim matches a verified true report
- **TIDAK SESUAI** - the claim matches a debunked hoax
- **MERAGUKAN** - partial or weak match, treat with care
- **TIDAK DITEMUKAN** - no verified reference close enough yet

Built for **HackGlobal 2026** (Polaris School of Technology, powered by Vultr),
Track 4: Civic and real-world impact. Solo build during the event window,
14-15 November 2026.

## The problem

Indonesia is one of the world's largest social media markets, and hoaxes spread
mostly as forwarded text: fake social-aid registration links, job scams,
recycled disaster videos, and health myths. Fact-checkers (Mafindo/TurnBackHoax,
CekFakta, Kominfo) have already verified thousands of these claims, but ordinary
users never search those databases. ClaimLens closes that gap: one paste, one
verdict, one source to read.

## How it works

1. The user pastes a claim in the web UI.
2. The backend tokenizes the text (Indonesian stopword filtering) and encodes it
   as a TF-IDF vector.
3. Cosine similarity retrieves the closest fact-check entries from the corpus
   (`data/claims.json`, seed corpus of Indonesian fact-checks with source links).
4. Similarity thresholds map the best match to a verdict, and the response
   always includes the matched claim, its fact-checker label, a plain-language
   summary, and the source URL.

No black-box verdicts: if nothing in the corpus is close enough, ClaimLens says
TIDAK DITEMUKAN instead of guessing.

**Language design:** the interface, docs, and submission are in English for the
global HackGlobal jury, while claims and the fact-check corpus stay in Bahasa
Indonesia, the language these hoaxes actually circulate in. Verdicts are shown
in English: MATCHES VERIFIED FACT, DEBUNKED, UNCERTAIN, NOT FOUND.

## System design

```
Browser (single-page UI)
        |  POST /api/check {claim}
        v
Flask backend (this repo)
        |-- TF-IDF index (pure Python, in-memory)
        |-- Corpus: data/claims.json (fact-check seed data)
        v
JSON verdict + matched reference + source URL
```

Deployed on a **Vultr Compute** instance (backend + static UI served by
gunicorn), which is also where the public demo URL lives.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## API

```bash
curl -X POST http://localhost:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"claim": "Vaksin COVID-19 mengandung microchip untuk melacak warga"}'
```

Response: verdict, similarity score, matched corpus entry, top-3 references,
and a plain-language explanation.

## Corpus and honesty notes

- The seed corpus ships with a starter set of well-known Indonesian
  fact-checks (health hoaxes, aid/job scams, recycled videos, and verified
  true reports). Each entry links back to its fact-checker so users can
  verify. Growing it toward the full TurnBackHoax database is the roadmap.
- ClaimLens is a triage aid, not a final arbiter of truth.

## Roadmap

- Import the full TurnBackHoax/Mafindo fact-check archive into the corpus
- Optional LLM/RAG explanation layer on top of the retrieved evidence
- WhatsApp-forward friendly share cards for each verdict
