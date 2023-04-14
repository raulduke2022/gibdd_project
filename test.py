from anticaptchaofficial.imagecaptcha import *  # captcha module
import base64
from fake_useragent import UserAgent
ua = UserAgent()
user_agent = ua.chrome
print(user_agent)

car_data = {
    'gosnomer': 'ВО85399',
    'model': 'Skoda Rapid',
    'office': 'Гудвей "Москва"',
    'vin': 'XW8AC2NH3MK139916'
}

def captcha_func(gosnomer):
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key("b78746e5f1f1678b4050533a1667e4be")
    solver.set_soft_id(0)
    answer = solver.solve_and_return_solution("imageToSave.png")
    return answer


def createa_img(image):
    with open(f"imageToSave.png", "wb") as fh:
        fh.write(base64.urlsafe_b64decode(image))





