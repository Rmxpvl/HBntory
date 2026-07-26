#!/usr/bin/env python3

from sqlalchemy import Column, Integer, String, Enum as SAEnum, DateTime, func, ForeignKey, CheckConstraint, UniqueConstraint
from .db import Base
from enum import Enum as PyEnum
from sqlalchemy.orm import relationship


class Branch(Base):
    __tablename__ = "branches"

    branch_id = Column(Integer, primary_key=True)
    localisation = Column(String, nullable=False)


    stocks = relationship("Stock", back_populates="branch")
    users = relationship("User", back_populates="branch")

class Role(PyEnum):
    COMMON = "Common"
    ADMIN = "Admin"


class UserStatus(PyEnum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"



class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False, unique=True)
    password_hash = Column(String,nullable=False)
    role = Column(SAEnum(Role, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id"), nullable=True)
    status = Column(SAEnum(UserStatus, values_callable=lambda enum_cls: [e.value for e in enum_cls]), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "(role = 'Admin' AND branch_id IS NULL) OR (role = 'Common' AND branch_id IS NOT NULL)"
        ),
        CheckConstraint(
            "(status != 'Active' OR deleted_at IS NULL)"
        ),
    )

    branch = relationship("Branch", back_populates="users")


class Stock(Base):
    __tablename__ = "stocks"

    stock_id = Column(Integer, primary_key=True)
    product_id = Column(Integer, nullable=False)
    branch_id = Column(Integer, ForeignKey("branches.branch_id"), nullable=False)
    quantity = Column(Integer, nullable=False)

    branch = relationship("Branch", back_populates="stocks")

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_stock_quantity"),
        UniqueConstraint(
            "branch_id",
            "product_id",
            name="uq_stock_branch_product"
        )
    )
