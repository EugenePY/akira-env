import os


class config:
    @staticmethod
    def get_env(name, default):
        return os.environ.get(name, default)

    @property
    def MONGODB_URI(cls):
        return cls.get_env("MONFODB_URI", "localhost:27017")

    @property
    def SCHEMA_REGISTRY(cls):
        return cls.get_env("SCHEMA_REGISTERY", "localhost:8081")

    @property
    def KAFKA_BOOSTRAP_HOST(cls):
        return cls.get_env("KAFKA_BOOSTRAP_HOST", "kafka://localhost:9092")
