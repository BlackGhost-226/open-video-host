from pool import Pool, ConnectionOptions
from asyncio import run

async def main():
    pool = Pool(ConnectionOptions("0.0.0.0", 5432, lambda: ("root", "abc123"))) # direct:5432 proxy:8080
    await pool.start()
    print(pool.size)
    rw = await pool.get()
    print(rw)
    print(pool.size)
    await pool.close()
    await pool.put(rw)
    print(pool.size)

if __name__ == "__main__":
    run(main())
