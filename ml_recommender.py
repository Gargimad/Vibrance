"""
ml_recommender.py — Unsupervised content-based recommendation.

Model:
    • TF-IDF vectorization of opportunity text (fit per request)
    • Cosine similarity between the user-profile vector and each
      opportunity vector
    • Ranked descending by similarity

No training, no persistence. The vectorizer is fit on whatever corpus
is in the DB at request time. This is the standard cold-start baseline
for recommendation systems and requires only scikit-learn.
"""

import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _get(row, key, default=""):
    try:
        v = row[key]
    except (KeyError, IndexError, TypeError):
        return default
    return default if v is None else v


def _clean(text):
    text = re.sub(r"[^\w\s]", " ", str(text).lower())
    return re.sub(r"\s+", " ", text).strip()


def _opp_doc(row):
    """One opportunity as a single document string."""
    return _clean(" ".join([
        _get(row, "title"),
        _get(row, "description"),
        _get(row, "activity"),
        _get(row, "required_skills"),
        _get(row, "location"),
        _get(row, "org_name"),
    ]))


def _user_doc(user_row, signup_rows, joined_org_rows):
    """The volunteer's interest profile as a single document string."""
    parts = [
        _get(user_row, "skills"),
        _get(user_row, "country"),
        _get(user_row, "zipcode"),
    ]
    for r in signup_rows:
        parts.append(_get(r, "activity"))
        parts.append(_get(r, "required_skills"))
    for r in joined_org_rows:
        parts.append(_get(r, "activity"))
    return _clean(" ".join(p for p in parts if p))


def rank_opportunities(user_row, signup_rows, joined_org_rows,
                       candidate_rows, top_n=6):
    """
    Returns (ranked_rows, scores) — same length, sorted by score desc.
    Excludes opportunities the volunteer has already signed up for.
    Falls back to soonest-upcoming when the user profile is empty.
    """
    if not candidate_rows:
        return [], []

    already = {
        _get(r, "opportunityID") for r in signup_rows
        if _get(r, "opportunityID")
    }
    candidates = [
        r for r in candidate_rows
        if _get(r, "opportunityID") not in already
    ]
    if not candidates:
        return [], []

    user_text = _user_doc(user_row, signup_rows, joined_org_rows)
    if not user_text:
        ordered = sorted(candidates,
                         key=lambda r: str(_get(r, "event_date", "")))
        top = ordered[:top_n]
        return top, [0.0] * len(top)

    docs = [_opp_doc(r) for r in candidates]
    try:
        vec = TfidfVectorizer(
            stop_words="english", min_df=1, ngram_range=(1, 2)
        )
        matrix = vec.fit_transform([user_text] + docs)
        scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    except ValueError:
        top = candidates[:top_n]
        return top, [0.0] * len(top)

    paired = sorted(zip(candidates, scores), key=lambda t: -t[1])
    top = paired[:top_n]
    return [r for r, _ in top], [float(s) for _, s in top]