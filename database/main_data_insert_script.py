import asyncpg
import asyncio
import pandas as pd
import sys
sys.path.append('/home/raulduke/Desktop/gibdd_project')

from gibdd_project.util.async_timer import async_timed

@async_timed()
async def select_query(key):
    return f'''
    SELECT model_id FROM models WHERE name = '{key}'
    '''

df = pd.read_excel(io='../cars_data/all_cars.xlsx')
cars = df.to_dict('records')

models_list = [car['Модель'] for car in cars]
models_list = set(models_list)
models_tuple = [(model,) for model in models_list]

@async_timed()
async def get_model_id(connection, model):
        model_int_query_request = await select_query(model)
        model_int = await connection.fetchval(model_int_query_request)
        return model_int
@async_timed()
async def insert_models(connection, models) -> int:
    insert_models = "INSERT INTO models VALUES(DEFAULT, $1)"
    return await connection.executemany(insert_models, models)
@async_timed()
async def insert_cars(connection, cars) -> int:
    insert_cars = "INSERT INTO cars VALUES(DEFAULT, $1, $2, $3, $4)"
    return await connection.executemany(insert_cars, cars)
@async_timed()
async def main():
    connection = await asyncpg.connect(host='127.0.0.1',
                                   port=5432,
                                   user='raulduke',
                                   password='kakacoarm',
                                   database='cars',
                                   )
    version = connection.get_server_version()
    print(f'Подключено! Версия Postgres равна {version}')
    await insert_models(connection, models_tuple)
    cars_list = []
    for car in cars:
        model_int = await get_model_id(connection, car['Модель'],)
        cars_list.append((car['Гос номер'], car['VIN'], car['Подразделение'], model_int))
    await insert_cars(connection, cars_list)

    print('job done')



asyncio.run(main())