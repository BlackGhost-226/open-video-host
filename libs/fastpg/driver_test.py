from driver.connection import Connection

conn = Connection("postgresql://root:test@0.0.0.0:8080/test") # direct:5432 proxy:8080
cur = conn.cursor()
cur.execute("select * from tbl1;")
print(cur.description)
print(cur.fetchall())
conn.commit()
cur.close()
conn.close()
