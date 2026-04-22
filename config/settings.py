import os

class Settings:
    BASE_PATH = "."
    
    DATA_PATH = "datos"
    BRONZE_PATH = os.path.join(DATA_PATH, "bronze")
    SILVER_PATH = os.path.join(DATA_PATH, "silver")
    GOLD_PATH = os.path.join(DATA_PATH, "gold")

    def get_bronze_path(self, fuente: str):
        path = os.path.join(self.BRONZE_PATH, fuente)
        os.makedirs(path, exist_ok=True)
        return path

settings = Settings()