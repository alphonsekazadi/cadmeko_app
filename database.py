# Connexion et helpers SQLAlchemy 
import mysql.connector
import os

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PWD", ""),
        database="cadmeko"
    )
