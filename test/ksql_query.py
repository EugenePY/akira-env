import logging
from ksql import KSQLAPI
logging.basicConfig(level=logging.DEBUG)
client = KSQLAPI('http://localhost:8088')
print(client.ksql('SHOW TOPICS;\nSHOW STREAMS;'))

table_name = "fx_rate"
topic = 'trading'
value_format = 'JSON'
columns_type = ['symbol VARCHAR', "date BIGINT", 'PX_LAST VARCHAR',
                "PX_OPEN VARCHAR", "PX_LOW VARCHAR", "PX_HIGH VARCHAR"]
try:
    res = client.create_stream(table_name=table_name,
                               columns_type=columns_type,
                               topic=topic,
                               value_format=value_format)
except Exception:
    print("TOPIC created")

print(client.ksql('SHOW TOPICS;\nSHOW STREAMS;\nSHOW TOPICS;'))

query = client.query("PRINT trading FROM BEGINNING LIMIT 5;")

for item in query:
    print(item)
