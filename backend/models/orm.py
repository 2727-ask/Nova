from sqlalchemy import Column, Integer, String, Float, UniqueConstraint, Index

from db.database import Base

class TransactionORM(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), index=True)
    description = Column(String(1024), index=True)
    amount = Column(Float, index=True)
    balance = Column(Float, nullable=True)
    category = Column(String(100), index=True)
    subcategory = Column(String(150), index=True)
    source = Column(String(50), default="chase_pdf")

    __table_args__ = (
        UniqueConstraint("date", "description", "amount", name="uq_txn_key"),
        Index("ix_txn_cat_sub", "category", "subcategory"),
    )