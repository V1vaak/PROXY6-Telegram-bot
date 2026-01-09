from datetime import datetime, timedelta

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
                                                 
    updated_at: Mapped[DateTime] = mapped_column(
                                    DateTime, 
                                    default=func.now(), 
                                    onupdate=func.now()
                                )

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    first_name: Mapped[str] = mapped_column(nullable=True)
    last_name: Mapped[str] = mapped_column(nullable=True)
    username: Mapped[str] = mapped_column(nullable=True)

class Proxy(Base):
    __tablename__ = 'proxies'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete="CASCADE"),
        index=True
    )
    
    ip: Mapped[str] = mapped_column(nullable=False)
    port: Mapped[str] = mapped_column(nullable=False)
    login: Mapped[str] = mapped_column(nullable=False)
    password: Mapped[str] = mapped_column(nullable=False)
    proxy_type: Mapped[str] = mapped_column(nullable=False)
    proxy_version: Mapped[str] = mapped_column(nullable=False)
    country: Mapped[str] = mapped_column(nullable=False)
    date_start: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    date_end: Mapped[DateTime] = mapped_column(DateTime, nullable=False)

    ids: Mapped[int] = mapped_column(nullable=False)

class Basket(Base):
    __tablename__ = 'baskets'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True
    )

    proxy_version: Mapped[int] = mapped_column(nullable=False)   
    proxy_type: Mapped[str] = mapped_column(nullable=False)      
    country: Mapped[str] = mapped_column(nullable=False)         

    count: Mapped[int] = mapped_column(nullable=False)
    period: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        CheckConstraint('count > 0', name='check_count_positive'),
        CheckConstraint('period >= 3', name='check_period_min'),
    )

class Spending(Base):
    __tablename__ = 'spendings'

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True
    )

    amount: Mapped[int] = mapped_column(nullable=False)  # в копейках
    currency: Mapped[str] = mapped_column(default='RUB')

    proxy_version: Mapped[int]
    proxy_type: Mapped[str]
    country: Mapped[str]
    count: Mapped[int]
    period: Mapped[int]

    payment_id: Mapped[str] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


class PriceCache(Base):
    __tablename__ = 'price_cache'

    id: Mapped[int] = mapped_column(primary_key=True)

    proxy_version: Mapped[int] = mapped_column(index=True)
    count: Mapped[int] = mapped_column(index=True)
    period: Mapped[int] = mapped_column(index=True)

    price_rub: Mapped[float] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    __table_args__ = (
        Index(
            'idx_price_cache_unique',
            'proxy_version',
            'count',
            'period',
            unique=True
        ),
    )

    def is_expired(self) -> bool:
        return datetime.utcnow() - self.updated_at > timedelta(days=1)