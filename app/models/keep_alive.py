from datetime import datetime, timezone

from sqlalchemy import BigInteger, Column, DateTime

from app.models.base import Base


class KeepAliveLog(Base):
    __tablename__ = "keep_alive_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
