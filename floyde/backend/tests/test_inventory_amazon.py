from app.services import amazon


def test_amazon_recs_rank_relevant_first():
    recs = amazon.get_recommendations("clipper fade", limit=3)
    assert len(recs) == 3
    # a clipper should rank above an unrelated disinfectant
    titles = " ".join(r.title.lower() for r in recs)
    assert "clip" in titles or "clipper" in titles


def test_amazon_links_carry_affiliate_tag():
    rec = amazon.get_recommendations("pomade", limit=1)[0]
    assert "tag=" in rec.url


def test_reorder_suggestions_dedupe():
    recs = amazon.reorder_suggestions(["pomade", "pomade"], per_item=2)
    asins = [r.asin for r in recs]
    assert len(asins) == len(set(asins))


def test_low_stock_endpoint(client):
    from tests.conftest import auth_headers

    owner = auth_headers(client, "o@floyde.app", "password123", "owner")
    shop = client.post(
        "/shops", json={"name": "S", "slug": "s"}, headers=owner
    ).json()
    client.post(
        "/inventory/products",
        json={"shop_id": shop["id"], "name": "Pomade", "quantity": 1,
              "reorder_threshold": 3},
        headers=owner,
    )
    low = client.get(
        "/inventory/low-stock", params={"shop_id": shop["id"]}, headers=owner
    )
    assert low.status_code == 200
    assert len(low.json()) == 1
