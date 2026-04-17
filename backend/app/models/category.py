# app/models/category.py
"""DocumentCategory ORM model — static lookup table for medical record types."""

from __future__ import annotations

from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class DocumentCategory(Base, TimestampMixin):
    """Static lookup / seed table for medical record types.

    Slugs: lab_report, prescription, imaging, discharge,
    vaccination, insurance, other.
    """

    __tablename__ = "document_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    icon_key: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DocumentCategory slug={self.slug}>"
