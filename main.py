from anticaptchaofficial.imagecaptcha import *  # captcha module
import base64  # make image from base64 string
from fake_useragent import UserAgent  # generate user-agent
import aiohttp
import asyncio
import aiofiles
import functools
from util.async_timer import async_timed
import logging
import asyncpg
import os
from database.sql_statements import insert_check_info, select_car

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

URL_CAPTCHA = 'https://check.gibdd.ru/captcha'
RESTRICT_URL = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/restrict'
DIAGNOSTIC_URL = 'https://xn--b1afk4ade.xn--90adear.xn--p1ai/proxy/check/auto/diagnostic'

# generating user-agent
ua = UserAgent()
user_agent = ua.chrome

# setting headers
HEADERS = {
    "User-Agent": 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Mobile Safari/537.36',
    "Accept": "application/json"
}


# ________________CAPTCHA FUNCTION____________________
@async_timed()
async def captcha_func(gosnomer):
    print('we are here')
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key("b78746e5f1f1678b4050533a1667e4be")
    solver.set_soft_id(0)
    loop = asyncio.get_event_loop()
    py_logger.info(f"Внутри catpcha_func() для {gosnomer}")
    future = loop.run_in_executor(
        None,
        functools.partial(solver.solve_and_return_solution,
                          file_path=f"{gosnomer}imageToSave.png"))
    try:
        captcha_text = await asyncio.wait_for(future, 120)
        py_logger.info(f"Решение {captcha_text} для {gosnomer}")
        return captcha_text
    except:
        py_logger.error(f"НЕТ ПОДКЛЮЧЕНИЯ К anticaptcha")
        return 0


@async_timed()
async def solve_captcha(session, pool, url, vin_nomer, gosnomer):
    while True:
        try:
            py_logger.info(f"Получаем капчу от гибдд для {gosnomer}")
            async with session.get(url, timeout=120) as resp:
                answer = await resp.json()
        except Exception as e:
            py_logger.error(f"Ошибка при получении капчи от гибдд {e} {gosnomer}")
            return
        else:
            py_logger.info(f"Решаем капчу для {gosnomer}")
            token = answer['token']
            image = answer['base64jpg']
            while True:
                try:
                    py_logger.info(f"Пробуем создать изображение из капчи {gosnomer}")
                    async with aiofiles.open(f"{gosnomer}imageToSave.png", "wb") as fh:
                        await fh.write(base64.urlsafe_b64decode(image))
                except Exception as e:
                    py_logger.error(f"Ошибка при создании изображении {e} для {gosnomer}")
                    continue
                else:
                    while True:
                        py_logger.info(
                            f"Запрос к anticaptcha для {gosnomer}")
                        captcha_text = await captcha_func(gosnomer)
                        if captcha_text:
                            data = {
                                "vin": vin_nomer,
                                "checkType": 'restricted',
                                "captchaWord": captcha_text,
                                "captchaToken": token
                            }
                            py_logger.info(
                                f"Делаем финальный запрос в гибдд для {gosnomer}")
                            async with session.post(DIAGNOSTIC_URL, data=data, timeout=120) as new_resp:
                                while True:
                                    try:
                                        result = await new_resp.json()
                                        if result.get('status') != 200:
                                            if result.get('code') == 201:
                                                py_logger.info(f"201 неправильное решение капчи для {gosnomer}")
                                                break
                                            else:
                                                py_logger.info(f"{result} для {gosnomer}, возврат")
                                                return
                                        else:
                                            os.remove(f"{gosnomer}imageToSave.png")
                                            py_logger.info(
                                                f"Ответ гибдд записан в бд: {new_resp.status} {result} {gosnomer}")
                                            car_id = await select_car(pool, gosnomer)
                                            if car_id:
                                                diagnostic_result = result.get('RequestResult').get('diagnosticCards')[
                                                    0]
                                                insert_data = (car_id, result.get('requestTime'),
                                                               bool(diagnostic_result),
                                                               diagnostic_result.get('dcExpirationDate'),
                                                               diagnostic_result.get('pointAddress'),
                                                               diagnostic_result.get('chassis'),
                                                               diagnostic_result.get('body'),
                                                               diagnostic_result.get('operatorName'),
                                                               diagnostic_result.get('odometerValue'),
                                                               diagnostic_result.get('dcNumber'),
                                                               diagnostic_result.get('dcDate'))
                                                await asyncio.create_task(insert_check_info(pool, insert_data))
                                                return
                                    except Exception as e:
                                        py_logger.info(
                                            f"Ошибка при выполнении запрос к гибдд {e} для {gosnomer}")
                                        return
                        else:
                            return


@async_timed()
async def main():
    async with asyncpg.create_pool(host='127.0.0.1',
                                   port=5432,
                                   user='raulduke',
                                   password='kakacoarm',
                                   database='cars') as pool:
        cars = await pool.fetch('SELECT * FROM cars;')
        py_logger.info(f"Начало процесса")
        connector = aiohttp.TCPConnector(limit_per_host=1)
        async with aiohttp.ClientSession(headers=HEADERS, connector=connector) as session:
            tasks = []
            for i in range(len(cars)):
                if i == 1:
                    break
                vin = cars[i]['vin_nomer']
                gos_nomer = cars[i]['gosnomer']
                tasks.append(solve_captcha(session, pool, URL_CAPTCHA, vin, gos_nomer))
            py_logger.info(f"Создали задачи и ждем через команду asyncio.gather")
            await asyncio.gather(*tasks, return_exceptions=False)


if __name__ == "__main__":
    py_logger.info(f"Запускаем asyncio.run(main()")
    asyncio.run(main())
