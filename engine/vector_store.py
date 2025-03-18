import weaviate
from weaviate.classes.init import Auth
import logging
import os
import dotenv

logger = logging.getLogger(__name__)
class WeaviateService:
    _instance = None

    def __new__(cls, weaviate_url, weaviate_api_key) -> "WeaviateService":
        if cls._instance is None:
            cls._instance = super(WeaviateService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, weaviate_url, weaviate_api_key) -> None:
        if self._initialized:
            return
        self.weaviate_url = weaviate_url
        self.weaviate_api_key = weaviate_api_key
        self.client = weaviate.connect_to_weaviate_cloud(cluster_url=self.weaviate_url, auth_credentials=Auth.api_key(self.weaviate_api_key))
        if self.client.is_ready():
            logger.info("⚡ Weaviate Client is ready")
        self._initialized = True

    @classmethod
    def get_instance(cls) -> "WeaviateService":
        if cls._instance is None:
            raise Exception("Instance not created yet. Call the constructor first.")
        return cls._instance
    

# Testing the WeaviateService class
if __name__ == "__main__":
    dotenv.load_dotenv()
    weaviate_url = os.environ["WEAVIATE_URL"]
    weaviate_api_key = os.environ["WEAVIATE_API_KEY"]
    weaviateService = WeaviateService(weaviate_url=weaviate_url, weaviate_api_key=weaviate_api_key)
    weaviateService.get_instance()
    print(weaviateService.client.is_ready())
    print(weaviateService.client.collections.delete_all())