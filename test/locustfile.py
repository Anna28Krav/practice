from locust import HttpUser, task, between

class BotUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def search_video(self):
        self.client.post("/search", json={"query": "test"})

    @task
    def get_favorites(self):
        self.client.get("/favorite")
