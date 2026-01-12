import uuid

from mountory_core.transactions.models import Transaction
from mountory_core.transactions.utils import calc_transactions_total


def test_calc_transactions_total_empty_collection() -> None:
    transactions: list[Transaction] = []

    res = calc_transactions_total(transactions)

    assert res == 0


def test_calc_transactions_total_transactions_without_amount() -> None:
    transactions = [Transaction() for _ in range(10)]

    res = calc_transactions_total(transactions)

    assert res == 0


def test_calc_transactions_total_transactions_with_amount_0() -> None:
    transactions = [Transaction(amount=0) for _ in range(10)]

    res = calc_transactions_total(transactions)

    assert res == 0


def test_calc_transactions_total_transactions_positive_amounts() -> None:
    amounts = range(0, 1000, 100)
    transactions = [Transaction(amount=amount) for amount in amounts]

    res = calc_transactions_total(transactions)

    assert res == sum(amounts)


def test_calc_transactions_total_transactions_negative_amounts() -> None:
    amounts = range(0, -1000, -100)
    transactions = [Transaction(amount=amount) for amount in amounts]

    res = calc_transactions_total(transactions)

    assert res == sum(amounts)


def test_calc_transactions_total_with_user_ids_empty_collection() -> None:
    user_id = uuid.uuid4()
    transactions: list[Transaction] = []

    res = calc_transactions_total(transactions, [user_id])

    assert res == 0


def test_calc_transactions_total_with_user_ids_no_match_amounts_0() -> None:
    user_id = uuid.uuid4()
    transactions = [Transaction(amount=0) for _ in range(10)]

    res = calc_transactions_total(transactions, [user_id])

    assert res == 0


def test_calc_transactions_total_with_user_ids_no_match_positive_amounts() -> None:
    user_id = uuid.uuid4()
    amounts = range(0, 1000, 100)
    transactions = [Transaction(amount=amount) for amount in amounts]

    res = calc_transactions_total(transactions, [user_id])

    assert res == 0


def test_calc_transactions_total_with_user_ids_no_match_negative_amounts() -> None:
    user_id = uuid.uuid4()
    amounts = range(0, 1000, 100)
    transactions = [Transaction(amount=amount) for amount in amounts]

    res = calc_transactions_total(transactions, [user_id])

    assert res == 0


def test_calc_transactions_total_with_user_ids_match_positive_amounts() -> None:
    user_id = uuid.uuid4()
    amounts = range(0, 1000, 100)

    transactions = [Transaction(user_id=user_id, amount=amount) for amount in amounts]
    transactions.extend(
        Transaction(amount=amount, user_id=uuid.uuid4())
        for amount in range(0, 500, 100)
    )
    transactions.extend(Transaction(amount=amount) for amount in range(500, 1000, 100))

    res = calc_transactions_total(transactions, [user_id])

    assert res == sum(amounts)


def test_calc_transactions_total_with_user_ids_match_negative_amounts() -> None:
    user_id = uuid.uuid4()
    amounts = range(0, -1000, -100)

    transactions = [Transaction(user_id=user_id, amount=amount) for amount in amounts]
    transactions.extend(
        Transaction(amount=amount, user_id=uuid.uuid4())
        for amount in range(0, -500, -100)
    )
    transactions.extend(
        Transaction(amount=amount) for amount in range(-500, -1000, -100)
    )

    res = calc_transactions_total(transactions, [user_id])

    assert res == sum(amounts)


def test_calc_transactions_total_with_user_ids_match_mixed_amounts() -> None:
    user_id = uuid.uuid4()
    amounts = (100, -12, 34, 500 - 0, +0, 200, -302)

    transactions = [Transaction(user_id=user_id, amount=amount) for amount in amounts]
    transactions.extend(
        Transaction(amount=amount, user_id=uuid.uuid4())
        for amount in (23, -43, 700, -1000)
    )
    transactions.extend(Transaction(amount=amount) for amount in (203, -43, -700, 1000))

    res = calc_transactions_total(transactions, [user_id])
    assert res == sum(amounts)
