"""Email notifications for match events (bids, acceptances, rejections).

All public functions are fire-and-forget safe — they catch exceptions
internally and log errors instead of propagating them.
"""

import asyncio
import logging

from google.cloud.firestore_v1 import AsyncClient

from app.services.email_service import send_html_email

logger = logging.getLogger(__name__)

# ── Shared helpers ──

_HEADER_STYLE = 'color: #2563eb; margin-bottom: 8px;'
_BODY_STYLE = 'font-family: Arial, sans-serif; max-width: 520px; margin: 0 auto; padding: 24px;'
_CARD_STYLE = 'background: #f0f9ff; border-radius: 12px; padding: 20px; margin: 16px 0;'
_MUTED_STYLE = 'color: #6b7280; font-size: 13px;'


async def _get_user_email(db: AsyncClient, uid: str) -> str | None:
    """Fetch the user's email from Firestore."""
    doc = await db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict().get("email")
    return None


async def _get_user_name(db: AsyncClient, uid: str) -> str:
    """Fetch the user's display name from Firestore."""
    doc = await db.collection("users").document(uid).get()
    if doc.exists:
        return doc.to_dict().get("full_name", "A user")
    return "A user"


async def _safe_send(to_email: str, subject: str, text: str, html: str) -> None:
    """Send email, swallowing errors so the caller is never blocked."""
    try:
        await send_html_email(to_email, subject, text, html)
        logger.info("Notification sent to %s: %s", to_email, subject)
    except Exception:
        logger.exception("Failed to send notification to %s: %s", to_email, subject)


# ── Public notification functions ──


async def notify_new_bid(
    db: AsyncClient,
    owner_uid: str,
    claimant_uid: str,
    listing_id: str,
    room_building: str | None = None,
    room_number: str | None = None,
) -> None:
    """Notify listing owner that someone placed a bid on their listing."""
    owner_email = await _get_user_email(db, owner_uid)
    if not owner_email:
        logger.warning("Cannot notify owner %s — no email found", owner_uid)
        return

    claimant_name = await _get_user_name(db, claimant_uid)
    room_label = f"{room_building} #{room_number}" if room_building and room_number else listing_id

    subject = f"New bid on your listing — {room_label}"
    text = (
        f"{claimant_name} has placed a bid on your room listing ({room_label}).\n\n"
        "Log in to the BIU Dorm Exchange platform to review and respond to this bid."
    )
    html = f"""\
    <div style="{_BODY_STYLE}">
        <h2 style="{_HEADER_STYLE}">New Bid Received 🏠</h2>
        <div style="{_CARD_STYLE}">
            <p style="margin: 0 0 8px; font-size: 15px;">
                <strong>{claimant_name}</strong> wants your room!
            </p>
            <p style="margin: 0; color: #374151; font-size: 14px;">
                Listing: <strong>{room_label}</strong>
            </p>
        </div>
        <p style="color: #374151; font-size: 14px;">
            Log in to the <strong>BIU Dorm Exchange</strong> platform to accept or reject this bid.
        </p>
        <p style="{_MUTED_STYLE}">
            If you didn't create this listing, you can safely ignore this email.
        </p>
    </div>
    """
    await _safe_send(owner_email, subject, text, html)


async def notify_swap_bid(
    db: AsyncClient,
    owner_uid: str,
    claimant_uid: str,
    listing_id: str,
    offered_category: str | None = None,
) -> None:
    """Notify listing owner that someone proposed a swap on their listing."""
    owner_email = await _get_user_email(db, owner_uid)
    if not owner_email:
        logger.warning("Cannot notify owner %s — no email found", owner_uid)
        return

    claimant_name = await _get_user_name(db, claimant_uid)
    category_label = offered_category or "their room"

    subject = "New swap proposal on your listing"
    text = (
        f"{claimant_name} has proposed a room swap, offering {category_label}.\n\n"
        "Log in to the BIU Dorm Exchange platform to review this swap proposal."
    )
    html = f"""\
    <div style="{_BODY_STYLE}">
        <h2 style="{_HEADER_STYLE}">Swap Proposal Received 🔄</h2>
        <div style="{_CARD_STYLE}">
            <p style="margin: 0 0 8px; font-size: 15px;">
                <strong>{claimant_name}</strong> wants to swap rooms with you!
            </p>
            <p style="margin: 0; color: #374151; font-size: 14px;">
                They're offering: <strong>{category_label}</strong>
            </p>
        </div>
        <p style="color: #374151; font-size: 14px;">
            Log in to the <strong>BIU Dorm Exchange</strong> platform to accept or reject this swap.
        </p>
        <p style="{_MUTED_STYLE}">
            If you didn't create this listing, you can safely ignore this email.
        </p>
    </div>
    """
    await _safe_send(owner_email, subject, text, html)


async def notify_bid_accepted(
    db: AsyncClient,
    claimant_uid: str,
    listing_id: str,
    room_building: str | None = None,
    room_number: str | None = None,
) -> None:
    """Notify claimant that their bid was accepted by the listing owner."""
    claimant_email = await _get_user_email(db, claimant_uid)
    if not claimant_email:
        logger.warning("Cannot notify claimant %s — no email found", claimant_uid)
        return

    room_label = f"{room_building} #{room_number}" if room_building and room_number else listing_id

    subject = f"Your bid was accepted! — {room_label}"
    text = (
        f"Great news! Your bid on listing {room_label} has been accepted.\n\n"
        "Log in to the BIU Dorm Exchange platform to view contact details and complete the exchange."
    )
    html = f"""\
    <div style="{_BODY_STYLE}">
        <h2 style="{_HEADER_STYLE}">Bid Accepted! 🎉</h2>
        <div style="background: #ecfdf5; border-radius: 12px; padding: 20px; margin: 16px 0;">
            <p style="margin: 0 0 8px; font-size: 15px; color: #065f46;">
                Your bid on <strong>{room_label}</strong> has been accepted!
            </p>
        </div>
        <p style="color: #374151; font-size: 14px;">
            Log in to the <strong>BIU Dorm Exchange</strong> platform to view the other party's
            contact details and coordinate the room exchange.
        </p>
        <p style="{_MUTED_STYLE}">
            Please complete the exchange process as soon as possible.
        </p>
    </div>
    """
    await _safe_send(claimant_email, subject, text, html)


async def notify_bid_rejected(
    db: AsyncClient,
    claimant_uid: str,
    listing_id: str,
    room_building: str | None = None,
    room_number: str | None = None,
) -> None:
    """Notify claimant that their bid was rejected by the listing owner."""
    claimant_email = await _get_user_email(db, claimant_uid)
    if not claimant_email:
        logger.warning("Cannot notify claimant %s — no email found", claimant_uid)
        return

    room_label = f"{room_building} #{room_number}" if room_building and room_number else listing_id

    subject = f"Bid update — {room_label}"
    text = (
        f"Unfortunately, your bid on listing {room_label} was not accepted.\n\n"
        "Don't worry — you can browse other available listings on the BIU Dorm Exchange platform."
    )
    html = f"""\
    <div style="{_BODY_STYLE}">
        <h2 style="{_HEADER_STYLE}">Bid Not Accepted</h2>
        <div style="background: #fef2f2; border-radius: 12px; padding: 20px; margin: 16px 0;">
            <p style="margin: 0 0 8px; font-size: 15px; color: #991b1b;">
                Your bid on <strong>{room_label}</strong> was not accepted this time.
            </p>
        </div>
        <p style="color: #374151; font-size: 14px;">
            Don't give up! Browse other available listings on the
            <strong>BIU Dorm Exchange</strong> platform.
        </p>
        <p style="{_MUTED_STYLE}">
            New listings are posted regularly — keep checking for your ideal room.
        </p>
    </div>
    """
    await _safe_send(claimant_email, subject, text, html)
