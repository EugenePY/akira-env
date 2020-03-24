from kafka import KafkaConsumer, TopicPartition, OffsetAndMetadata
from kafka.partitioner.default import murmur2
import json
import datetime
import logging
# logging.basicConfig(level=logging.DEBUG)


# To consume latest messages and auto-commit offsets

TOPIC = "trading_new"
consumer1 = KafkaConsumer(group_id="agent-1",
                          value_deserializer=lambda m: json.loads(
                              m.decode("utf-8")),
                          bootstrap_servers=['localhost:9092'],
                          enable_auto_commit=False,
                          session_timeout_ms=10000,
                          auto_offset_reset='earliest')
tp = TopicPartition(TOPIC, 0)
# consume json messages
# for message in consumer1:
#    # message value and key are raw bytes -- decode if necessary!
# e.g., for unicode: `message.value.decode('utf-8')`
#    print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
#                                         message.offset, message.key,
#                                         message.value))

# consumer1.close()
#
consumer1.assign([tp])
datetime_offset = int((datetime.datetime.utcnow() - datetime.timedelta(days=1)
                       ).timestamp()*1000)

pos = consumer1.position(tp)
print("[most recent offset]=", pos)
# print(datetime_offset)
# print(consumer1.offsets_for_times({tp: datetime_offset}))
# offset = consumer1.beginning_offsets([tp])
# print(offset)
# consumer1.poll()
# go to end of the stream
# consumer1.seek_to_end()
#meta = consumer1.partitions_for_topic(TOPIC)
offset = consumer1.end_offsets([tp])
# print(consumer1.committed(tp))
# consumer1.seek_to_beginning(tp)
#consumer1.poll(offset[tp]-1)
#consumer1.commit({tp: OffsetAndMetadata(offset[tp]-1, None)})
consumer1.seek(tp, offset[tp] - 1)
for message in consumer1:
    #    # message value and key are raw bytes -- decode if necessary!
    # e.g., for unicode: `message.value.decode('utf-8')`
    # print(datetime.datetime.fromtimestamp(message.timestamp/1000) -
    #      datetime.timedelta(hours=8))
    print("%s:%d:%d: timestamp=%i key=%s value=%s" % (message.topic,
                                                      message.partition,
                                                      message.offset,
                                                      message.timestamp,
                                                      message.key,
                                                      message.value))
    raise

consumer1.close(autocommit=False)
