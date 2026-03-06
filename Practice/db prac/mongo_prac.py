from pymongo import MongoClient

# Подключение к MongoDB
client = MongoClient("localhost", 27017)
db = client["my_database"]
collection = db["my_collection"]

# Создание документа
documents = [
    {"name": "Alice", "age": 30, "email": "alice@example.com"},
    {"name": "Bob", "age": 25, "email": "bob@example.com"},
    {"name": "Charlie", "age": 35, "email": "charlie@example.com"},
]


# Вставка документа
collection.delete_many({})
result = collection.insert_many([document for document in documents])


# Поиск документа
found_document = collection.find_one({"name": "Alice"})

# Закрытие соединения
client.close()
