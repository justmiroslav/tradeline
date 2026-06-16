from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, ForeignKey, Numeric, Boolean, text, Text, DateTime, Index
from sqlalchemy import Enum as SAEnum, PrimaryKeyConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from domain.enums import Exchange, MarketType, TradeSide, PositionSide, PositionStatus, PlanTier

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    plan: Mapped[PlanTier] = mapped_column(SAEnum(PlanTier), default=PlanTier.FREE, nullable=False)
    token_version: Mapped[int] = mapped_column(default=1, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(512))
    last_ai_insight: Mapped[Optional[str]] = mapped_column(Text)
    last_ai_insight_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_ai_verified: Mapped[Optional[bool]] = mapped_column(Boolean)
    last_ai_feedback: Mapped[Optional[bool]] = mapped_column(Boolean)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255))
    subscription_status: Mapped[Optional[str]] = mapped_column(String(32))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    api_keys: Mapped[list[ApiKey]] = relationship(back_populates="user", cascade="all, delete-orphan")
    trades: Mapped[list[Trade]] = relationship(back_populates="user", cascade="all, delete-orphan")
    positions: Mapped[list[Position]] = relationship(back_populates="user", cascade="all, delete-orphan")

class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_user", "user_id"),
        Index("ix_api_keys_next_check", "next_check_at")
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    account_uid: Mapped[Optional[str]] = mapped_column(String(64))
    label: Mapped[Optional[str]] = mapped_column(String(64))
    api_key_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    passphrase_encrypted: Mapped[Optional[str]] = mapped_column(String(512))
    capabilities: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    ip_restricted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String(512))
    last_error_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ws_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    next_check_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    user: Mapped[User] = relationship(back_populates="api_keys")

class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (
        PrimaryKeyConstraint("id", "time"),
        UniqueConstraint("user_id", "trade_id", "exchange", "market_type", "time", name="uq_trade_exchange_id"),
        Index("ix_trades_user_time", "user_id", "time"),
        Index("ix_trades_user_symbol_time", "user_id", "symbol", "time"),
        Index("ix_trades_api_key_time", "api_key_id", "time")
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    api_key_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("api_keys.id", ondelete="CASCADE"))
    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[TradeSide] = mapped_column(SAEnum(TradeSide), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    quote_qty: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    fee_asset: Mapped[Optional[str]] = mapped_column(String(16))
    realized_pnl: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    is_maker: Mapped[Optional[bool]] = mapped_column(Boolean)
    position_side: Mapped[Optional[str]] = mapped_column(String(8))
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    order_id: Mapped[Optional[str]] = mapped_column(String(64))
    trade_id: Mapped[str] = mapped_column(String(64), nullable=False)

    user: Mapped[User] = relationship(back_populates="trades")

class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (
        Index("uq_position_open", "user_id", "api_key_id", "exchange", "market_type", "symbol", "side",
              unique=True, postgresql_where=text("status = 'OPEN'")),
        Index("ix_positions_user_closed", "user_id", "closed_at"),
        Index("ix_positions_user_status", "user_id", "status"),
        Index("ix_positions_api_key", "api_key_id"),
        Index("ix_positions_unlinked", "exchange", "market_type", "symbol", postgresql_where=text("setup IS NULL")),
        Index("ix_positions_key_symbol", "api_key_id", "symbol", "opened_at")
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    api_key_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("api_keys.id", ondelete="CASCADE"))
    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    side: Mapped[PositionSide] = mapped_column(SAEnum(PositionSide), nullable=False)
    status: Mapped[PositionStatus] = mapped_column(SAEnum(PositionStatus), nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    entry_notional: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=0, nullable=False)
    exit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    realized_pnl: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=0, nullable=False)
    fees_quote: Mapped[Decimal] = mapped_column(Numeric(38, 18), default=0, nullable=False)
    entry_fills: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    trade_count: Mapped[int] = mapped_column(default=0, nullable=False)
    setup: Mapped[Optional[str]] = mapped_column(String(32))
    mfe: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    mae: Mapped[Optional[Decimal]] = mapped_column(Numeric(38, 18))
    averaged_down: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped[User] = relationship(back_populates="positions")

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_type_time", "type", "created_at"),
        Index("ix_events_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    type: Mapped[str] = mapped_column(String(48), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        Index("ix_reviews_status", "status", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    rating: Mapped[int] = mapped_column(nullable=False)
    body: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

    user: Mapped[User] = relationship()

class RefreshSession(Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (
        Index("ix_refresh_sessions_user", "user_id"),
    )

    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    prev_jti: Mapped[Optional[str]] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

class EmailCode(Base):
    __tablename__ = "email_codes"
    __table_args__ = (
        Index("ix_email_codes_user_purpose", "user_id", "purpose", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    purpose: Mapped[str] = mapped_column(String(32), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

class MarketUniverse(Base):
    __tablename__ = "market_universe"
    __table_args__ = (
        PrimaryKeyConstraint("exchange", "market_type", "symbol"),
    )

    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    activated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    last_klines_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

class MarketKline(Base):
    __tablename__ = "market_klines"
    __table_args__ = (
        PrimaryKeyConstraint("exchange", "market_type", "symbol", "time"),
    )

    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(38, 18), nullable=False)

class MarketSetup(Base):
    __tablename__ = "market_setups"
    __table_args__ = (
        PrimaryKeyConstraint("exchange", "market_type", "symbol", "time"),
    )

    exchange: Mapped[Exchange] = mapped_column(SAEnum(Exchange), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(SAEnum(MarketType), nullable=False)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    setup: Mapped[str] = mapped_column(String(32), nullable=False)
    context: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))

