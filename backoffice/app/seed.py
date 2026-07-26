#!/usr/bin/env python3

import os

from argon2 import PasswordHasher

from .db import SessionLocal
from .models import (
    Branch,
    User,
    Role,
    UserStatus,
    Stock,
)

db = SessionLocal()

branch_Annecy = db.query(Branch).filter_by(localisation="Annecy").first()

if branch_Annecy is None:
    branch_Annecy= Branch(
        localisation="Annecy"
    )
    db.add(branch_Annecy)
    db.commit()
    db.refresh(branch_Annecy)

branch_Thonon = db.query(Branch).filter_by(localisation="Thonon-les-bains").first()

if branch_Thonon is None:
    branch_Thonon = Branch(
        localisation="Thonon-les-bains"
    )
    db.add(branch_Thonon)
    db.commit()
    db.refresh(branch_Thonon)

branch_Geneve = db.query(Branch).filter_by(localisation="Geneve").first()

if branch_Geneve is None:
    branch_Geneve = Branch(
        localisation="Geneve"
    )
    db.add(branch_Geneve)
    db.commit()
    db.refresh(branch_Geneve)



ph = PasswordHasher()
existing_admin = db.query(User).filter_by(username="admin").first()

if existing_admin is None:
    admin_password_hash = ph.hash(os.environ["ADMIN_PASSWORD"])
    admin = User(
        username="admin",
        password_hash=admin_password_hash,
        role=Role.ADMIN,
        status=UserStatus.ACTIVE,
    )
    db.add(admin)
    db.commit()



stock_Annecy = db.query(Stock).filter_by(branch_id=branch_Annecy.branch_id, product_id=1).first()
if stock_Annecy is None:
    stock = Stock(
        product_id=1,
        branch_id=branch_Annecy.branch_id,
        quantity=50,
    )
    db.add(stock)
    db.commit()

stock_Thonon = db.query(Stock).filter_by(branch_id=branch_Thonon.branch_id, product_id=1).first()
if stock_Thonon is None:
    stock = Stock(
        product_id=1,
        branch_id=branch_Thonon.branch_id,
        quantity=30,
    )
    db.add(stock)
    db.commit()

stock_Geneve = db.query(Stock).filter_by(branch_id=branch_Geneve.branch_id, product_id=1).first()
if stock_Geneve is None:
    stock = Stock(
        product_id=1,
        branch_id=branch_Geneve.branch_id,
        quantity=20,
    )
    db.add(stock)
    db.commit()
