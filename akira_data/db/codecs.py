from schema_registry.client import SchemaRegistryClient, schema
from schema_registry.serializers import FaustSerializer
from akira_data.setting import config
import os
# create an instance of the `SchemaRegistryClient`

client = SchemaRegistryClient(url="http://" +
                              os.environ.get("SCHEMA_REGISTRY", "localhost:8081"))

# schema that we want to use. For this example we
# are using a dict, but this schema could be located in a file called avro_user_schema.avsc

avro_ticker_schema = schema.AvroSchema({
    "type": "record",
    "namespace": "akira.data",
    "name": "AvroTicker",
    "fields": [
        {"name": "data", "type": "string"},
        {"name": "symbol", "type": "string"},
        {"name": "index", "type": "string",
         "doc": "should be in datetime format"}
    ]
})
schema_id = client.register(avro_ticker_schema.name.lower(), avro_ticker_schema)

avro_ticker_serializer = FaustSerializer(client, avro_ticker_schema.name.lower(),
                                         avro_ticker_schema)

avro_metadata_schema = schema.AvroSchema({
    "type": "record",
    "namespace": "akira.data",
    "name": "AvroMetadata",
    "fields": [
        {"name": "metadata", "type": {"type": "map", "values": "string"}},
        {"name": "symbol", "type": "string"},
        {"name": "index", "type": "string", "doc": "should be in datetime format"}
    ]
})


# function used to register the codec
def avro_ticker_codec():
    return avro_ticker_serializer
