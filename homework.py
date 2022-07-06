import logging
import os
import sys
import time
from http import HTTPStatus
from typing import Optional

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

from exceptions import BotError, ResponseKeyError

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

API_KEYS = {"current_date", "homeworks"}

HOMEWORK_STATUSES = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stdout_handler = logging.StreamHandler(stream=sys.stdout)
formatter = logging.Formatter(
    "%(asctime)s %(filename)s/%(funcName)s [%(levelname)s] %(message)s"
)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)


def send_message(bot: Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат.

    Чат определяется переменной окружения data:`TELEGRAM_CHAT_ID`

    Args:
        bot (telegram.Bot): Бот, оправляющий сообщения
        message (str): Сообщение
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
    except TelegramError as err:
        logger.error(err)
    else:
        logger.info(f"Сообщение успешно отправлено: {message}")


def get_api_answer(timestamp: int = int(time.time())) -> dict:
    """Делает запрос к API yandex.practicum.

    Args:
       timestamp (int): начальное время

    Returns:
        dict: ответ API

    Raises:
        requests.exceptions.RequestException
    """
    params = {"from_date": timestamp}

    response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    if response.status_code != HTTPStatus.OK:
        raise requests.exceptions.RequestException(
            f"HTTP status code не равен {HTTPStatus.OK}: "
            f"{response.reason} ({response.status_code})"
        )

    return response.json()


def check_response(response: dict) -> list:
    """Проверяет ответ API на корректность.

    Args:
        response (dict): yandex.practicum API response

    Returns:
        list: список домашних работ (он может быть и пустым),
              доступный в ответе API по ключу 'homeworks'.

    Raises:
        ResponseKeyError: если в ответе отсутствует обязательный ключ
            или если в ответе присутствует недокументированный ключ
        TypeError: если тип объектов не совпадает с заданным
    """
    if not isinstance(response, dict):
        raise TypeError("Ответ (response) API должен иметь тип 'dict'")

    missed_keys = API_KEYS - set(response.keys())
    if missed_keys:
        raise ResponseKeyError(
            missed_keys, "В ответе API нет обязательных ключей"
        )

    unexpected_keys = set(response.keys()) - API_KEYS
    if unexpected_keys:
        raise ResponseKeyError(
            unexpected_keys, "В ответе API есть недокументированные ключи"
        )

    if not isinstance(response.get("homeworks"), list):
        raise TypeError("В ответе API 'homeworks' должен иметь тип 'list'")

    return response.get("homeworks", [])


def parse_status(homework: dict) -> Optional[str]:
    """Извлекает из информации о конкретной домашней работе статус этой работы.

    Args:
        homework (dict): элемент из списка домашних работ

    Returns:
        str: подготовленную для отправки в Telegram строку,
             содержащую один из вердиктов словаря HOMEWORK_STATUSES
    """
    homework_name = str(homework.get("homework_name", ""))
    homework_status = str(homework.get("status"))

    try:
        verdict = HOMEWORK_STATUSES[homework_status]
    except KeyError:
        raise KeyError(
            f"Недокументированный статус проверки домашней работы: "
            f'"{homework_status}"'
        )

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения, необходимых для работы.

    Returns:
        bool:   True  - если все переменные окруждения заданы,
                False - если хотя бы одна переменная окружения не задана
                (т.е. равна None)
    """
    tokens_to_check = (
        PRACTICUM_TOKEN,
        TELEGRAM_TOKEN,
        TELEGRAM_CHAT_ID,
    )

    return None not in tokens_to_check


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical(
            "Не заданы переменные окружения! Работа бота невозможна!"
        )
        exit()

    bot = Bot(token=TELEGRAM_TOKEN)

    current_timestamp = int(time.time())
    cached_error = ""
    was_error = False

    while True:
        try:
            response = get_api_answer(current_timestamp)

            homeworks = check_response(response)

            message = "\n\n".join(parse_status(h) for h in homeworks)

        except requests.exceptions.RequestException as err:
            message = f"Недоступен endpoint API yandex.practicum: {err}"
            logger.error(message)
            was_error = True

        except BotError as err:
            message = str(err)
            logger.error(message)
            was_error = True

        except Exception as err:
            message = f"Сбой в работе программы: {err}"
            logger.error(message)
            was_error = True

        if not message:
            logger.debug("Статус проверки домашней работы не изменился")
        elif was_error:
            if message != cached_error:
                send_message(bot, message)
                cached_error = message
        else:
            send_message(bot, message)

        current_timestamp = int(time.time())

        time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
