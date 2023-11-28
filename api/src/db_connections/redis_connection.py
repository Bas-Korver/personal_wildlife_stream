import redis


class RedisConnection:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance.redis_client = redis.Redis(host="",
                                                      password="",
                                                      decode_responses=True)
        return cls.__instance

    def get_redis_client(self):
        return self.redis_client
