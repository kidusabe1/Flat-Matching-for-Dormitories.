from datetime import date, datetime, timezone

from google.cloud.firestore_v1 import AsyncClient


def _dates_overlap(a_start, a_end, b_start, b_end) -> bool:
    """Check if two date ranges overlap by at least 1 day."""
    # Normalize to date objects
    def to_date(val):
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, date):
            return val
        return val

    a_s, a_e = to_date(a_start), to_date(a_end)
    b_s, b_e = to_date(b_start), to_date(b_end)
    return a_s <= b_e and b_s <= a_e


async def find_compatible_lease_transfers(
    db: AsyncClient,
    category: str | None = None,
    building: str | None = None,
    min_start: date | None = None,
    max_end: date | None = None,
    exclude_uid: str | None = None,
    limit: int = 20,
) -> list[dict]:
    query = db.collection("listings")
    query = query.where("listing_type", "==", "LEASE_TRANSFER")
    query = query.where("status", "==", "OPEN")

    if category:
        query = query.where("room_category", "==", category)
    if building:
        query = query.where("room_building", "==", building)

    query = query.limit(limit * 2)

    results = []
    async for doc in query.stream():
        data = doc.to_dict()
        data["id"] = doc.id
        if exclude_uid and data["owner_uid"] == exclude_uid:
            continue
        if min_start:
            doc_start = data["lease_start_date"]
            if isinstance(doc_start, datetime):
                doc_start = doc_start.date()
            if doc_start < min_start:
                continue
        if max_end:
            doc_end = data["lease_end_date"]
            if isinstance(doc_end, datetime):
                doc_end = doc_end.date()
            if doc_end > max_end:
                continue
        results.append(data)
        if len(results) >= limit:
            break

    return results


async def find_compatible_swaps(
    db: AsyncClient,
    listing_id: str,
    limit: int = 20,
) -> list[dict]:
    """Find swap listings compatible with the given listing.

    Compatible means:
    1. Their room category is in my desired_categories
    2. My room category is in their desired_categories
    3. Date ranges overlap
    4. Building preferences match (if specified)
    5. Status is OPEN or PARTIAL_MATCH
    6. Not owned by the same user
    """
    listing_doc = await db.collection("listings").document(listing_id).get()
    if not listing_doc.exists:
        return []
    listing = listing_doc.to_dict()
    listing["id"] = listing_doc.id

    desired_cats = listing.get("desired_categories", [])
    if not desired_cats:
        return []

    candidates = []
    seen_ids = set()

    for desired_cat in desired_cats:
        query = (
            db.collection("listings")
            .where("listing_type", "==", "SWAP_REQUEST")
            .where("status", "in", ["OPEN", "PARTIAL_MATCH"])
            .where("room_category", "==", desired_cat)
            .limit(limit * 3)
        )
        async for doc in query.stream():
            if doc.id not in seen_ids:
                data = doc.to_dict()
                data["id"] = doc.id
                candidates.append(data)
                seen_ids.add(doc.id)

    compatible = []
    for c in candidates:
        if c["owner_uid"] == listing["owner_uid"]:
            continue
        if c["id"] == listing_id:
            continue
        # Reverse check: does candidate want MY room category?
        c_desired = c.get("desired_categories", [])
        if listing["room_category"] not in c_desired:
            continue
        # Building preferences
        c_buildings = c.get("desired_buildings")
        if c_buildings and listing["room_building"] not in c_buildings:
            continue
        my_buildings = listing.get("desired_buildings")
        if my_buildings and c["room_building"] not in my_buildings:
            continue
        # Date overlap
        if not _dates_overlap(
            listing["lease_start_date"],
            listing["lease_end_date"],
            c["lease_start_date"],
            c["lease_end_date"],
        ):
            continue
        compatible.append(c)
        if len(compatible) >= limit:
            break

    return compatible
