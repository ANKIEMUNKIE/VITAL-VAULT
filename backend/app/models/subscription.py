# app/models/subscription.py
"""Subscription and SubscriptionTier ORM models."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class SubscriptionTier(Base, TimestampMixin):
    """Static lookup table for subscription plan tiers.

    Seed data: free, pro, b2b.
    """

    __tablename__ = "subscription_tiers"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    slug: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    storage_quota_bytes: Mapped[int] = mapped_column(
        BigInteger, nullable=False
    )
    max_reminders: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    ai_summaries_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    price_monthly_cents: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    def __repr__(self) -> str:
        return f"<SubscriptionTier slug={self.slug}>"


class Subscription(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User subscription linking to a specific tier.

    Integrates with Stripe for paid tiers.
    """

    __tablename__ = "subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tier_id: Mapped[int] = mapped_column(Integer, ForeignKey("subscription_tiers.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, default="ACTIVE", server_default="ACTIVE"
    )
    current_period_end: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    stripe_customer_id: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    stripe_sub_id: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    # --- Relationships (string refs to avoid circular imports) ---
    user = relationship("User", back_populates="subscriptions")
    tier = relationship("SubscriptionTier", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Subscription id={self.id} tier_id={self.tier_id} status={self.status}>"
