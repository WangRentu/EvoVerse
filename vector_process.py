from evoverse.knowledge.vector_db import get_vector_db
from evoverse.config import get_config

cfg = get_config()
print("Chroma dir:", cfg.knowledge.chroma_persist_directory)

db = get_vector_db()
print("Before clear:", db.get_stats())

db.clear()

print("After clear:", db.get_stats())

# print("chromadb stats:", db.get_stats())