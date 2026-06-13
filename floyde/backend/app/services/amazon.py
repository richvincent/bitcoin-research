"""Amazon product intelligence.

Returns ranked product recommendations for barbershop supplies. When PA-API
credentials are absent, falls back to a curated offline catalog so the
feature is useful out of the box (and affiliate-tagged links still work).

Real PA-API v5 signing is non-trivial; the live path is left as a clearly
marked integration point. The offline path is fully functional.
"""

from __future__ import annotations

from app.config import settings
from app.schemas.schemas import AmazonRec

# Curated, barber-relevant catalog. `{tag}` is replaced with the affiliate
# partner tag at request time so links are monetizable immediately.
_CATALOG: list[dict] = [
    {
        "asin": "B000142FVW", "title": "Wahl Professional 5-Star Magic Clip Cordless",
        "brand": "Wahl", "price": "$99.99", "rating": 4.8, "review_count": 21450,
        "keywords": ["clipper", "fade", "cordless", "tool"],
    },
    {
        "asin": "B07GR4T6M2", "title": "Andis Professional T-Outliner Trimmer",
        "brand": "Andis", "price": "$69.95", "rating": 4.7, "review_count": 18230,
        "keywords": ["trimmer", "lineup", "edge", "tool"],
    },
    {
        "asin": "B00MR4OLO0", "title": "BaBylissPRO Barberology MetalFX Clipper",
        "brand": "BaBylissPRO", "price": "$129.99", "rating": 4.6, "review_count": 9120,
        "keywords": ["clipper", "fade", "tool", "premium"],
    },
    {
        "asin": "B07PKCJ4M8", "title": "Suavecito Pomade Original Hold 4 oz",
        "brand": "Suavecito", "price": "$13.49", "rating": 4.7, "review_count": 33010,
        "keywords": ["pomade", "styling", "product", "retail"],
    },
    {
        "asin": "B003V265QW", "title": "Layrite Original Pomade 4 oz",
        "brand": "Layrite", "price": "$18.00", "rating": 4.8, "review_count": 12760,
        "keywords": ["pomade", "styling", "product", "retail"],
    },
    {
        "asin": "B07QK1N6R3", "title": "King C. Gillette Beard Oil 30 ml",
        "brand": "Gillette", "price": "$9.97", "rating": 4.5, "review_count": 8800,
        "keywords": ["beard", "oil", "grooming", "product", "retail"],
    },
    {
        "asin": "B0148NPHL2", "title": "Barber Neck Duster Brush",
        "brand": "Diane", "price": "$7.49", "rating": 4.6, "review_count": 5400,
        "keywords": ["duster", "accessory", "supply"],
    },
    {
        "asin": "B07 B2J5N8K", "title": "Disposable Neck Strips (5 rolls)",
        "brand": "Marvy", "price": "$11.99", "rating": 4.8, "review_count": 6210,
        "keywords": ["neck strips", "supply", "consumable", "sanitation"],
    },
    {
        "asin": "B000WYJTGM", "title": "Barbicide Disinfectant Concentrate 16 oz",
        "brand": "Barbicide", "price": "$10.95", "rating": 4.9, "review_count": 14300,
        "keywords": ["disinfectant", "sanitation", "supply", "consumable"],
    },
]


def _affiliate_url(asin: str) -> str:
    return f"https://www.amazon.com/dp/{asin}?tag={settings.amazon_partner_tag}"


def _to_rec(item: dict) -> AmazonRec:
    asin = item["asin"].replace(" ", "")
    return AmazonRec(
        asin=asin,
        title=item["title"],
        brand=item.get("brand", ""),
        price=item.get("price", ""),
        rating=item.get("rating"),
        review_count=item.get("review_count"),
        url=_affiliate_url(asin),
        image_url=f"https://images-na.ssl-images-amazon.com/images/P/{asin}.jpg",
    )


def get_recommendations(query: str, *, limit: int = 5) -> list[AmazonRec]:
    """Rank recommendations for a free-text query (product name, category)."""
    if settings.amazon_enabled:
        # Integration point: call PA-API v5 SearchItems here, then map to
        # AmazonRec. Falls through to the curated catalog until wired.
        pass

    terms = {t for t in query.lower().split() if t}
    scored: list[tuple[int, dict]] = []
    for item in _CATALOG:
        hay = (item["title"] + " " + " ".join(item["keywords"])).lower()
        score = sum(1 for t in terms if t in hay)
        # light boost for highly-reviewed, well-rated items
        score = score * 10 + int(item.get("rating", 0) * 2)
        scored.append((score, item))

    scored.sort(key=lambda s: s[0], reverse=True)
    return [_to_rec(item) for _, item in scored[:limit]]


def reorder_suggestions(low_stock_names: list[str], *, per_item: int = 2) -> list[AmazonRec]:
    """Given names of low-stock products, suggest Amazon restock options."""
    recs: list[AmazonRec] = []
    seen: set[str] = set()
    for name in low_stock_names:
        for rec in get_recommendations(name, limit=per_item):
            if rec.asin not in seen:
                seen.add(rec.asin)
                recs.append(rec)
    return recs
