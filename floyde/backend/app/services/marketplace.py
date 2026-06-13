"""Marketplace helpers: slugging and rating aggregation."""

from __future__ import annotations

import re

from sqlmodel import Session, func, select

from app.models import Provider, Review

_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    return _slug_re.sub("-", name.lower()).strip("-")


def unique_slug(session: Session, name: str) -> str:
    base = slugify(name) or "provider"
    slug = base
    i = 2
    while session.exec(select(Provider).where(Provider.slug == slug)).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def recompute_rating(session: Session, provider: Provider) -> Provider:
    """Refresh a provider's cached average rating + review count."""
    avg, count = session.exec(
        select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.provider_id == provider.id
        )
    ).one()
    provider.rating = round(float(avg), 2) if avg is not None else 0.0
    provider.review_count = int(count or 0)
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider
