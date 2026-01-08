import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from mountory_core.transactions import crud
from mountory_core.transactions.models import (
    TransactionCreate,
    TransactionUpdate,
    Transaction,
)
from sqlmodel import Session
from unittest.mock import MagicMock, AsyncMock

import pytest


def test_create_transaction_commit_default() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data)

    db.commit.assert_called_once()


def test_create_transaction_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data, commit=True)

    db.commit.assert_called_once()


def test_create_transaction_no_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionCreate()

    _ = crud.create_transaction(db=db, data=data, commit=False)

    db.commit.assert_not_called()


def test_update_transaction_commit_default() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data)

    db.commit.assert_called_once()


def test_update_transaction_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data, commit=True)

    db.commit.assert_called_once()


def test_update_transaction_no_commit() -> None:
    db = MagicMock(spec=Session)
    data = TransactionUpdate()
    transaction = Transaction()

    _ = crud.update_transaction(db=db, transaction=transaction, data=data, commit=False)

    db.commit.assert_not_called()


@pytest.mark.anyio
async def test_delete_transaction_by_id_commit_default() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(db=db, transaction_id=transaction_id)

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_transaction_by_id_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(
        db=db, transaction_id=transaction_id, commit=True
    )

    db.commit.assert_called_once()


@pytest.mark.anyio
async def test_delete_transaction_by_id_no_commit() -> None:
    db = AsyncMock(spec=AsyncSession)
    transaction_id = uuid.uuid4()

    await crud.delete_transaction_by_id(
        db=db, transaction_id=transaction_id, commit=False
    )

    db.commit.assert_not_called()
