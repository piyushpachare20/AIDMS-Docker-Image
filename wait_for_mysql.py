import time
import pymysql
import os

host = os.environ.get("MYSQL_HOST", "mysql_db")

port = int(os.environ.get("MYSQL_PORT", 3306))
user = os.environ.get("MYSQL_USER", "root")
password = os.environ.get("MYSQL_PASSWORD", "")
database = os.environ.get("MYSQL_DATABASE", "")

max_retries = 10

for i in range(max_retries):
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        print("✅ MySQL is ready!")
        connection.close()
        break
    except pymysql.err.OperationalError as e:
        print(f"⏳ Waiting for MySQL... ({i + 1}/{max_retries}) - {e}")
        time.sleep(3)
else:
    print("❌ Could not connect to MySQL after several retries.")
    exit(1)
