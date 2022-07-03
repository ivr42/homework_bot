import logging
import os
import sys
import time
from typing import Dict, List

import requests
from dotenv import load_dotenv
from telegram import Bot, ReplyKeyboardMarkup, Update
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater,
)

load_dotenv()
PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}

RESPONSE = {
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


def send_message(bot, message):
    pass


def get_api_answer(timestamp: int = int(time.time())) -> dict:
    """Делает запрос к API yandex.practicum.

    Args:
       timestamp (int): начальное время

    Returns:
        dict: ответ API
    """
    params = {"from_date": timestamp}

    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)

    except requests.exceptions.RequestException as err:
        logger.error(f"Недоступен endpoint API yandex.practicum: {err}")
        return {}

    if not response.ok:
        logger.error(
            f"Недоступен endpoint API yandex.practicum: "
            f"{response.reason} ({response.status_code})"
        )
        return {}

    return response.json()


def check_response(response: dict) -> list:
    """Проверяет ответ API на корректность.

    Args:
        response (dict): yandex.practicum API response

    Returns:
        list: список домашних работ (он может быть и пустым),
              доступный в ответе API по ключу 'homeworks'.
    """
    # отсутствие ожидаемых ключей в ответе API (уровень ERROR);

    return response.get("homeworks") or list()


def parse_status(homework):
    # homework_name = ...
    # homework_status = ...

    # ...

    # verdict = ...

    # ...

    # return f"Изменился статус проверки работы "{homework_name}". {verdict}"
    pass


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

    from pprint import pprint

    api_answer = get_api_answer(int(time.time()) - 30 * 60 * 60 * 24)
    pprint(check_response(api_answer))

    # bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())

    # # ...

    # while True:
    #     try:
    #         response = ...

    #         ...

    #         current_timestamp = ...
    #         time.sleep(RETRY_TIME)

    #     except Exception as error:
    #         message = f"Сбой в работе программы: {error}"
    #         ...
    #         time.sleep(RETRY_TIME)
    #     else:
    #         ...


if __name__ == "__main__":
    main()
