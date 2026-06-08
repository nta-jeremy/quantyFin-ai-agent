import threading
from neo4j import GraphDatabase
from app.core.config import settings

class Neo4jSessionManager:
    def __init__(self):
        self._driver = None
        self._lock = threading.Lock()

    def get_driver(self):
        if self._driver is None:
            with self._lock:
                if self._driver is None:
                    self._driver = GraphDatabase.driver(
                        settings.NEO4J_URI,
                        auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                    )
        return self._driver

    def close(self):
        with self._lock:
            if self._driver is not None:
                self._driver.close()
                self._driver = None

neo4j_manager = Neo4jSessionManager()

def get_neo4j_session():
    driver = neo4j_manager.get_driver()
    with driver.session() as session:
        yield session
