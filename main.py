from anticaptchaofficial.imagecaptcha import *  # captcha module
import base64  # make image from base64 string
from fake_useragent import UserAgent  # generate user-agent
import pandas as p
import aiohttp
import asyncio
import aiofiles
import functools
from util.async_timer import async_timed
import requests
import logging
import json
import asyncpg
import os

# _______________________DATABASE________________________

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


async def insert_check_info(pool, data):
    async with pool.acquire() as connection:
        await connection.execute(statement, data)


# _______________________Logging______________________


# получение пользовательского логгера и установка уровня логирования
py_logger = logging.getLogger(__name__)
py_logger.setLevel(logging.INFO)

# настройка обработчика и форматировщика в соответствии с нашими нуждами
py_handler = logging.FileHandler(f"{__name__}.log", mode='w')
py_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")

# добавление форматировщика к обработчику
py_handler.setFormatter(py_formatter)
# добавление обработчика к логгеру
py_logger.addHandler(py_handler)

py_logger.info(f"Testing the custom logger for module {__name__}...")

# ___________________________________________________


URL_CAPTCHA = 'https://check.gibdd.ru/captcha'
RESTRICT_URL = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/restrict'
DIAGNOSTIC_URL = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'
FREE_PROXIES = []

# generating user-agent
ua = UserAgent()
user_agent = ua.chrome

# setting headers
HEADERS = {
    "User-Agent": 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36',
    "Accept": "application/json"
}


# py_logger.info(f"Открываем файл источник где автомобили")
# df = p.read_excel(io='cars_data/cars.xlsx')
# cars = df.to_dict('records')


# ________________CAPTCHA FUNCTION____________________
@async_timed()
async def captcha_func(gosnomer):
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key("b78746e5f1f1678b4050533a1667e4be")
    solver.set_soft_id(0)
    loop = asyncio.get_event_loop()
    py_logger.info(f"Пробуем получить решение капчи через функцию catpcha_func() для {gosnomer}")
    future = loop.run_in_executor(
        None,
        functools.partial(solver.solve_and_return_solution,
                          file_path=f"{gosnomer}imageToSave.png"))
    captcha_text = await asyncio.wait_for(future, 60)
    py_logger.info(f"Получили решение {captcha_text} капчи возвращаем в основную задачу solve_captcha для {gosnomer}")
    return captcha_text


@async_timed()
async def solve_captcha(session, pool, url, vin_nomer, gosnomer):
    try:
        py_logger.info(f"Пробуем получить капчу через обращение к гибдд {gosnomer}")
        async with session.get(url) as resp:
            answer = await resp.json()
    except Exception as e:
        py_logger.error(f"Если не получилось, пробуем еще раз потому что была ошибка {e} {gosnomer}")
        return
    else:
        py_logger.info(f"У нас получилось! Приступаем к решению капчи {gosnomer}")
        token = answer['token']
        image = answer['base64jpg']
        while True:
            try:
                py_logger.info(f"Пробуем создать изображение из капчи {gosnomer}")
                async with aiofiles.open(f"{gosnomer}imageToSave.png", "wb") as fh:
                    await fh.write(base64.urlsafe_b64decode(image))
            except Exception as e:
                py_logger.error(f"Если не получилось, пробуем еще раз потому что была ошибка {e} {gosnomer}")
                continue
            else:
                py_logger.info(
                    f"У нас получилось! Далаем запрос через await к anticaptcha для решения капчи {gosnomer}")
                captcha_text = await captcha_func(gosnomer)
                if captcha_text:
                    py_logger.info(
                        f"Получили решение капчи в виде цифр, составляет тело запроса для гибдд {gosnomer}")
                    data = {
                        "vin": vin_nomer,
                        "checkType": 'restricted',
                        "captchaWord": captcha_text,
                        "captchaToken": token
                    }
                    new_data = json.dumps(data)
                    py_logger.info(
                        f"Пробуем сделать запрос гибдд для получения информации по автомобилю {gosnomer}")

                    new_url = f'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic?vin={vin_nomer}&checkType=restricted&captchaWord={captcha_text}&captchaToken={token}'
                    async with session.post(DIAGNOSTIC_URL, data=data) as new_resp:
                        while True:
                            try:
                                new_answer = await asyncio.wait_for(new_resp.json(), 60)
                                if new_answer.get('status') != 200:
                                    if new_answer.get(
                                            'message') == 'Проверка CAPTCHA не была пройдена, поскольку не был передан ее код.':
                                        continue
                                    print(new_answer)
                                    py_logger.info(
                                        f"Если ответ 201 значит неправильно решили, значит придется заново делать запрос к anticaptcha для решения капчи {gosnomer}")
                                    break
                                else:
                                    os.remove(f"{gosnomer}imageToSave.png")
                                    py_logger.info(
                                        f"Все ок! Вот ответ от гибдд: {new_resp.status} {new_answer} {gosnomer}")
                                    py_logger.info(f"Завершаем процедуру по данному автомобилю {gosnomer}")
                                    car_id = await pool.fetchrow(f"SELECT car_id FROM cars WHERE gosnomer = '{gosnomer}'")['car_id']
                                    return (car_id, '1', bool(1), '1', '1', '1', '1', '1', '1', '1', '1')
                            except Exception as e:
                                py_logger.info(
                                    f"Получили такой ответ от гибдд {e} для {gosnomer}. Повторяем запрос post для получения информации")
                                print(e.args[0])
                                return


@async_timed()
async def main():
    async with asyncpg.create_pool(host='127.0.0.1',
                                   port=5432,
                                   user='postgres',
                                   password='kakacoarm',
                                   database='postgres') as pool:
        cars = await pool.fetch('SELECT * FROM cars;')
    py_logger.info(f"Начало процесса")
    connector = aiohttp.TCPConnector(limit_per_host=1)
    async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
        tasks = []
        for i in range(len(cars)):
            if i == 5:
                break
            vin = cars[i]['vin_nomer']
            gos_nomer = cars[i]['gosnomer']
            tasks.append(solve_captcha(session, pool, URL_CAPTCHA, vin, gos_nomer))
        py_logger.info(f"Создали задачи и ждем через команду asyncio.gather")
        results = await asyncio.gather(*tasks, return_exceptions=False)
        tasks_insert = []
        for data in results:
            tasks_insert.append(insert_check_info(pool, *data))
        await asyncio.gather(*tasks_insert)




if __name__ == "__main__":
    py_logger.info(f"Запускаем asyncio.run(main()")
    asyncio.run(main())
