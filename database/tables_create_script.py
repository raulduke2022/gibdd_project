import asyncpg
import asyncio

CREATE_MODELS_TABLE = \
"""
CREATE TABLE IF NOT EXISTS models(
model_id SERIAL PRIMARY KEY,
name TEXT NOT NULL
);
"""



CREATE_CARS_TABLE = \
"""
CREATE TABLE IF NOT EXISTS cars(
car_id SERIAL PRIMARY KEY,
gosnomer TEXT NOT NULL,
vin_nomer TEXT NOT NULL, 
office TEXT NOT NULL,
model INT NOT NULL,
CONSTRAINT fk_model
FOREIGN KEY(model) 
REFERENCES models(model_id)
);
"""

CREATE_CHECKS_TABLE = \
"""
CREATE TABLE IF NOT EXISTS checks(
check_id SERIAL PRIMARY KEY,
car INT,
check_date TEXT,
diagnosticCards BOOLEAN NOT NULL, 
dcExpirationDate TEXT,
pointAddress TEXT,
chassis TEXT,
body TEXT,
operatorName TEXT,
odometerValue TEXT,
dcNumber TEXT,
dcDate TEXT,
CONSTRAINT fk_car
FOREIGN KEY(car) 
REFERENCES cars(car_id)
);
"""

# async def insert_models(connection, brands) -> int:
#     insert_brands = "INSERT INTO models VALUES(DEFAULT, $1)"
#     return await connection.executemany(insert_brands, brands)

async def main():
    connection = await asyncpg.connect(host='localhost',
                                       port=5432,
                                       user='raulduke',
                                       database='cars',
                                       password='kakacoarm')
    version = connection.get_server_version()
    print(f'Подключено! Версия Postgres равна {version}')
    await connection.execute(CREATE_MODELS_TABLE)
    await connection.execute(CREATE_CARS_TABLE)
    await connection.execute(CREATE_CHECKS_TABLE)
    await connection.close()
    print('job done')



asyncio.run(main())

