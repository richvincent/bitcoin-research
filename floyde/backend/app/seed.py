"""Seed demo data: a Detroit shop, two barbers, services, a client profile.

Run with:  python -m app.seed
Idempotent-ish: skips seeding if the demo shop already exists.
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.core.security import hash_password
from app.database import engine, init_db
from app.models import (
    Barber,
    ClientProfile,
    ConciergeRequest,
    Offering,
    Product,
    Provider,
    ProviderCategory,
    Review,
    Service,
    Shop,
    User,
    UserRole,
)
from app.services import marketplace

DEMO_SLUG = "mayberry-cuts"


def seed() -> None:
    init_db()
    with Session(engine) as s:
        if s.exec(select(Shop).where(Shop.slug == DEMO_SLUG)).first():
            print("Demo data already present — nothing to do.")
            return

        owner = User(
            email="owner@floyde.app",
            hashed_password=hash_password("password123"),
            full_name="Floyd Lawson",
            role=UserRole.OWNER,
        )
        client = User(
            email="client@floyde.app",
            hashed_password=hash_password("password123"),
            full_name="Andy Taylor",
            role=UserRole.CLIENT,
        )
        b1_user = User(
            email="barber1@floyde.app",
            hashed_password=hash_password("password123"),
            full_name="Floyd Jr.",
            role=UserRole.BARBER,
        )
        b2_user = User(
            email="barber2@floyde.app",
            hashed_password=hash_password("password123"),
            full_name="Howard Sprague",
            role=UserRole.BARBER,
        )
        s.add_all([owner, client, b1_user, b2_user])
        s.commit()
        for u in (owner, client, b1_user, b2_user):
            s.refresh(u)

        shop = Shop(
            name="Mayberry Cuts",
            slug=DEMO_SLUG,
            owner_id=owner.id,
            address="123 Main St, Detroit, MI",
            latitude=42.3314,
            longitude=-83.0458,
        )
        s.add(shop)
        s.commit()
        s.refresh(shop)

        barbers = [
            Barber(
                user_id=b1_user.id, shop_id=shop.id, display_name="Floyd Jr.",
                bio="Skin fades and classic tapers.", rating=4.9,
                specialties=["skin fade", "taper", "lineup", "beard"],
            ),
            Barber(
                user_id=b2_user.id, shop_id=shop.id, display_name="Howard",
                bio="Scissor work and textured crops.", rating=4.6,
                specialties=["scissor", "textured top", "crop"],
            ),
        ]
        services = [
            Service(shop_id=shop.id, name="Signature Haircut", duration_minutes=45,
                    price_cents=4500, tags=["skin fade", "taper", "haircut"]),
            Service(shop_id=shop.id, name="Beard Trim", duration_minutes=20,
                    price_cents=2000, tags=["beard", "lineup"]),
            Service(shop_id=shop.id, name="The Distinguished (Cut + Beard)",
                    duration_minutes=60, price_cents=6500,
                    tags=["skin fade", "beard", "premium"]),
        ]
        products = [
            Product(shop_id=shop.id, name="Suavecito Pomade", brand="Suavecito",
                    quantity=2, reorder_threshold=3, cost_cents=800,
                    price_cents=1600, amazon_asin="B07PKCJ4M8"),
            Product(shop_id=shop.id, name="Neck Strips", brand="Marvy",
                    quantity=10, reorder_threshold=4, cost_cents=600,
                    price_cents=0),
        ]
        profile = ClientProfile(
            user_id=client.id,
            phone="+13135550100",
            preferred_styles=["skin fade", "beard", "low maintenance"],
            style_notes="Leave a bit of length on top. Sensitive skin on neck.",
            nuances={"top_guard": 3, "sides_guard": 1, "allergies": ["menthol"]},
            preferred_products=["Suavecito Pomade"],
            loyalty_points=120,
        )
        s.add_all([*barbers, *services, *products, profile])
        s.commit()

        # ── Marketplace providers (listed by the shop owner) ──
        providers = [
            Provider(
                name="Detroit Barber Supply Co.", slug="detroit-barber-supply",
                category=ProviderCategory.SUPPLIES, created_by=owner.id,
                location="Detroit, MI",
                description="Wholesale clippers, blades, capes, and consumables.",
                website="https://example.com/dbs",
                contact_email="sales@dbs.example",
            ),
            Provider(
                name="ShearShield Insurance", slug="shearshield-insurance",
                category=ProviderCategory.INSURANCE, created_by=owner.id,
                location="Remote",
                description="Liability + booth-rental coverage built for barbers.",
                website="https://example.com/shearshield",
            ),
            Provider(
                name="ChairFull Marketing", slug="chairfull-marketing",
                category=ProviderCategory.MARKETING, created_by=owner.id,
                description="Local SEO and rebooking campaigns for shops.",
            ),
        ]
        s.add_all(providers)
        s.commit()
        for p in providers:
            s.refresh(p)

        s.add_all([
            Offering(provider_id=providers[0].id, title="Wahl Magic Clip (case of 6)",
                     price_cents=54000, unit="per case"),
            Offering(provider_id=providers[0].id, title="Disposable capes (500)",
                     price_cents=8900, unit="per box"),
            Offering(provider_id=providers[1].id, title="Pro liability plan",
                     price_cents=3900, unit="per month"),
            Offering(provider_id=providers[2].id, title="Rebooking automation",
                     price_cents=14900, unit="per month"),
        ])
        # A couple of reviews from the seeded client.
        s.add_all([
            Review(provider_id=providers[0].id, author_id=client.id, rating=5,
                   title="Fast shipping", body="Next-day on blades. Great prices."),
            Review(provider_id=providers[1].id, author_id=client.id, rating=4,
                   title="Solid coverage", body="Easy signup, fair rates."),
        ])
        s.commit()
        for p in providers:
            marketplace.recompute_rating(s, p)

        # ── A demo concierge request waiting at the desk ──
        s.add(
            ConciergeRequest(
                client_id=client.id,
                shop_id=shop.id,
                phone="+13135550100",
                topic="Help me pick a style for a wedding",
            )
        )
        s.commit()

        print("Seeded demo data:")
        print(f"  Shop: {shop.name} (#{shop.id})")
        print("  Login (all): password123")
        print("    owner@floyde.app / client@floyde.app / barber1@floyde.app")


if __name__ == "__main__":
    seed()
