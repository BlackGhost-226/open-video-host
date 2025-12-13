from snowflake import SnowflakeGenerator, Snowflake
from base64 import urlsafe_b64encode

sf = Snowflake.parse(856165981072306191, 1288834974657)
gen = SnowflakeGenerator.from_snowflake(sf)

for i in range(2):
    val = next(gen)
    raw = val.to_bytes(8, byteorder="big")
    id = urlsafe_b64encode(raw).rstrip(b'=').decode()
    print(val)
    print(id)
