from ozzb2b_api.config import get_settings

s = get_settings()
print("events_enabled =", s.events_enabled)
print("events_stream_name =", s.events_stream_name)
print("events_stream_maxlen =", s.events_stream_maxlen)
print("clickhouse_url =", s.clickhouse_url)
print("clickhouse_database =", s.clickhouse_database)
print("redis_url (masked) =", s.redis_url.replace("@", "@... "))
