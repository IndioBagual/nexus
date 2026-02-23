from nexus.adapters.sqlite.connection import SQLiteConnection
from nexus.domain.entities import Task
from nexus.domain.ports import TaskRepository


class TaskSQLiteRepo(TaskRepository):
    def __init__(self, conn: SQLiteConnection):
        self.conn = conn

    def add(self, task: Task) -> int:
        with self.conn.get_cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (title, priority, status, due_date, created_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    task.title,
                    task.priority,
                    task.status,
                    task.due_date,
                    task.created_at,
                ),
            )
            task.id = cursor.lastrowid
            return task.id
