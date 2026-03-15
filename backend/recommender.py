"""Core recommendation engine with similarity reasons."""

from models import SimilarityReason


def compute_reasons(
    source: dict,
    candidate: dict,
    source_meta: dict | None,
    candidate_meta: dict | None,
) -> list[SimilarityReason]:
    """Generate human-readable reasons for why two movies are similar."""
    reasons: list[SimilarityReason] = []

    # Genre overlap
    source_genres = set(source.get("genres", []))
    candidate_genres = set(candidate.get("genres", []))
    shared_genres = source_genres & candidate_genres
    if shared_genres:
        reasons.append(SimilarityReason(
            reason="Shared genres",
            detail=", ".join(sorted(shared_genres)),
        ))

    # Same language
    if source.get("language") == candidate.get("language") and source.get("language") != "en":
        lang_names = {
            "hi": "Hindi", "ta": "Tamil", "te": "Telugu",
            "ml": "Malayalam", "kn": "Kannada", "ko": "Korean",
            "ja": "Japanese", "fr": "French", "es": "Spanish",
        }
        lang = lang_names.get(source["language"], source["language"])
        reasons.append(SimilarityReason(
            reason="Same language",
            detail=lang,
        ))

    if source_meta and candidate_meta:
        # Same director
        s_director = source_meta.get("director")
        c_director = candidate_meta.get("director")
        if s_director and c_director and s_director == c_director:
            reasons.append(SimilarityReason(
                reason="Same director",
                detail=s_director,
            ))

        # Shared cast
        s_cast = {c["name"] for c in (source_meta.get("cast_members") or [])}
        c_cast = {c["name"] for c in (candidate_meta.get("cast_members") or [])}
        shared_cast = s_cast & c_cast
        if shared_cast:
            names = sorted(shared_cast)[:3]
            reasons.append(SimilarityReason(
                reason="Shared cast",
                detail=", ".join(names),
            ))

        # Shared keywords
        s_kw = set(source_meta.get("keywords") or [])
        c_kw = set(candidate_meta.get("keywords") or [])
        shared_kw = s_kw & c_kw
        if shared_kw:
            kws = sorted(shared_kw)[:3]
            reasons.append(SimilarityReason(
                reason="Similar themes",
                detail=", ".join(kws),
            ))

    # Similar rating
    s_rating = source.get("vote_average", 0)
    c_rating = candidate.get("vote_average", 0)
    if s_rating > 0 and c_rating > 0 and abs(s_rating - c_rating) < 1.0:
        reasons.append(SimilarityReason(
            reason="Similar rating",
            detail=f"{c_rating:.1f}/10",
        ))

    # If no specific reasons found, fall back to plot similarity
    if not reasons:
        reasons.append(SimilarityReason(
            reason="Similar plot",
            detail="Based on story and themes",
        ))

    return reasons
