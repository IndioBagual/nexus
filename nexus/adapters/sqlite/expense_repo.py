from nexus.adapters.sqlite.connection import SQLiteConnection
from nexus.domain.entities import Expense
from nexus.domain.ports import ExpenseRepository


class ExpenseSQLiteRepo(ExpenseRepository):
    def __init__(self, conn: SQLiteConnection):
        self.conn = conn

    def add(self, expense: Expense) -> int:
        with self.conn.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO expenses (amount, category, description, currency, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    expense.amount,
                    expense.category,
                    expense.description,
                    expense.currency,
                    expense.created_at,
                ),
            )
            expense.id = cursor.lastrowid
            return expense.id
