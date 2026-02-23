
import requests


class APIClient:
    def __init__(self, base_url="http://localhost:8000/api"):
        self.base_url = base_url

    def get_agenda(self):
        try:
            return requests.get(f"{self.base_url}/chronos/today").json()
        except:
            return []

    def get_finances(self):
        try:
            return requests.get(f"{self.base_url}/treasury/summary").json()
        except:
            return {}

    def get_rpg_status(self):
        try:
            return requests.get(f"{self.base_url}/rpg/status").json()
        except:
            return {}

    def post_task(self, title, priority="medium", due_date=None):
        return requests.post(
            f"{self.base_url}/chronos/tasks",
            json={"title": title, "priority": priority, "due_date": due_date},
        ).json()

    def post_expense(self, amount, category, description):
        return requests.post(
            f"{self.base_url}/treasury/expenses",
            json={"amount": amount, "category": category, "description": description},
        ).json()

    def post_note(self, title, content, tags=[]):
        return requests.post(
            f"{self.base_url}/library/notes",
            json={"title": title, "content": content, "tags": tags},
        ).json()
