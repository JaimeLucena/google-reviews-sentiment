# streamlit_app.py
import math
import requests
import streamlit as st
import pandas as pd

API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Sentiment Analyzer", page_icon="🧠", layout="wide")

st.title("🧠 Sentiment Analyzer (LangChain + FastAPI)")
st.caption("Analyze raw text or real Google business reviews — powered by LCEL.")

mode = st.radio("Choose a mode:", ["Analyze text", "Analyze place"], horizontal=True)

def label_badge(label: str) -> str:
    color = {"positive": "green", "neutral": "gray", "negative": "red"}.get(label, "blue")
    return f"<span style='background:{color};color:white;padding:3px 8px;border-radius:12px;font-size:0.85rem'>{label}</span>"

def score_to_pct(score: float) -> int:
    # -1..1 -> 0..100
    return round((score + 1) * 50)

def aggregate(results: list[dict]) -> dict:
    if not results:
        return {"avg": 0.0, "counts": {"positive": 0, "neutral": 0, "negative": 0}, "top_aspects": []}
    total = 0.0
    counts = {"positive": 0, "neutral": 0, "negative": 0}
    aspect_scores: dict[str, list[float]] = {}
    for r in results:
        total += r["score"]
        counts[r["label"]] = counts.get(r["label"], 0) + 1
        for a in r.get("aspects", []):
            aspect_scores.setdefault(a["aspect"], []).append(a["score"])
    avg = total / len(results)
    aspects = [
        {"aspect": a, "avg_score": sum(v) / len(v), "mentions": len(v)}
        for a, v in aspect_scores.items()
    ]
    aspects.sort(key=lambda x: (-x["mentions"], -x["avg_score"]))
    return {"avg": avg, "counts": counts, "top_aspects": aspects[:8]}

if mode == "Analyze text":
    st.subheader("Analyze arbitrary text")
    colL, colR = st.columns([2, 1])
    with colL:
        txt = st.text_area("Text to analyze", height=160, placeholder="Paste one or more reviews...")
    with colR:
        lang = st.selectbox("Language hint", ["auto (None)", "en", "es"], index=2)
        model = st.text_input("Model (optional)", value="")
        btn = st.button("Analyze text", type="primary")

    if btn:
        payload = {
            "texts": [t.strip() for t in txt.split("\n") if t.strip()] if txt else [],
            "language_hint": None if lang.startswith("auto") else lang,
        }
        if model.strip():
            payload["model_name"] = model.strip()

        if not payload["texts"]:
            st.warning("Please enter at least one line of text.")
        else:
            try:
                r = requests.post(f"{API_BASE}/analyze/text", json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                results = data["results"]
                agg = aggregate(results)

                st.markdown(f"**Average sentiment:** `{agg['avg']:.2f}`  •  "
                            f"Counts → 👍 {agg['counts']['positive']}  | 😐 {agg['counts']['neutral']}  | 👎 {agg['counts']['negative']}")

                # Aspects table (if any)
                if agg["top_aspects"]:
                    df = pd.DataFrame(agg["top_aspects"])
                    st.dataframe(df, use_container_width=True)

                st.divider()
                st.subheader("Individual results")
                for r in results:
                    st.markdown(f"{label_badge(r['label'])} &nbsp; **Score:** `{r['score']:.2f}`  &nbsp; **Pct:** {score_to_pct(r['score'])}%", unsafe_allow_html=True)
                    st.write(r["text"])
                    if r.get("rationale"):
                        st.caption(f"Rationale: {r['rationale']}")
                    if r.get("aspects"):
                        chips = " ".join([label_badge(f"{a['aspect']} ({a['label']})") for a in r["aspects"]])
                        st.markdown(chips, unsafe_allow_html=True)
                    st.markdown("---")
            except requests.HTTPError as e:
                st.error(f"API error: {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")

else:
    st.subheader("Analyze a Google place (search by name)")
    colL, colR = st.columns([2, 1])
    with colL:
        query = st.text_input("Place query", placeholder="e.g., 'El Tigre Madrid'").strip()
    with colR:
        limit = st.slider("Max reviews", min_value=1, max_value=5, value=5)
        language = st.selectbox("Reviews language (Google)", ["es", "en", "fr", "de"], index=0)
        model = st.text_input("Model (optional)", value="")
    go = st.button("Analyze place", type="primary")

    if go:
        payload = {"query": query, "limit": limit, "language": language}
        if model.strip():
            payload["model_name"] = model.strip()

        if not query:
            st.warning("Please provide a place query.")
        else:
            try:
                r = requests.post(f"{API_BASE}/google/analyze-by-query", json=payload, timeout=60)
                r.raise_for_status()
                data = r.json()
                results = data["results"]
                agg = aggregate(results)

                st.markdown(f"**Place ID:** `{data['place_id']}`")
                st.markdown(f"**Reviews analyzed:** `{data['review_count']}`")
                st.markdown(f"**Average sentiment:** `{agg['avg']:.2f}`  •  "
                            f"Counts → 👍 {agg['counts']['positive']}  | 😐 {agg['counts']['neutral']}  | 👎 {agg['counts']['negative']}")

                if agg["top_aspects"]:
                    st.subheader("Top aspects")
                    df = pd.DataFrame(agg["top_aspects"])
                    st.dataframe(df, use_container_width=True)

                st.divider()
                st.subheader("Reviews")
                for r in results:
                    st.markdown(f"{label_badge(r['label'])} &nbsp; **Score:** `{r['score']:.2f}`  &nbsp; **Pct:** {score_to_pct(r['score'])}%", unsafe_allow_html=True)
                    st.write(r["text"])
                    if r.get("rationale"):
                        st.caption(f"Rationale: {r['rationale']}")
                    if r.get("aspects"):
                        chips = " ".join([label_badge(f"{a['aspect']} ({a['label']})") for a in r["aspects"]])
                        st.markdown(chips, unsafe_allow_html=True)
                    st.markdown("---")
            except requests.HTTPError as e:
                st.error(f"API error: {e.response.text}")
            except Exception as e:
                st.error(f"Unexpected error: {e}")