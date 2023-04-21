import asyncio
import asyncpg

some_date = (1, '1', bool(1), '1', '1', '1', '1', '1', '1', '1','1')

statement = """INSERT INTO checks (car,
                           check_date, 
                           diagnosticcards, 
                           dcexpirationdate, 
                           pointaddress,
                           chassis,
                           body,
                           operatorname,
                           odometervalue,
                           dcnumber,
                           dcdate) VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11);"""

statement1 = "SELECT car_id FROM cars WHERE gosnomer = 'АХ05534'"
print(statement1)
async def query_product(pool):
    async with pool.acquire() as connection:
        return await connection.fetchrow(statement1)


async def main():
    async with asyncpg.create_pool(host='127.0.0.1',
                                   port=5432,
                                   user='postgres',
                                   password='kakacoarm',
                                   database='postgres') as pool:
        task = asyncio.create_task(query_product(pool))
        result = await task
        print(result)


asyncio.run(main())