# _______________________DATABASE________________________

insert_into_checks = """INSERT INTO checks (car,
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




async def insert_check_info(pool, data):
    async with pool.acquire() as connection:
        await connection.execute(insert_into_checks, *data)

async def select_car(pool, gosnomer):
    select_car = f"SELECT car_id FROM cars WHERE gosnomer = '{gosnomer}'"
    async with pool.acquire() as connection:
        result = await connection.fetchrow(select_car)
        if result:
            return result['car_id']
        return False


