import logging
import os
import sys
import time
from typing import Optional

import requests
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError

from exceptions import BotError, HomeworkStatusError, ResponseError, ResponseKeyError

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
    print("TELEGRAM: ", message)

    # try:
    #     bot.send_message(
    #         chat_id=TELEGRAM_CHAT_ID,
    #         text=message,
    #     )
    # except TelegramError as err:
    #     logger.error(err)
    # else:
    #     logger.info(f"Сообщение успешно отправлено: {message}")


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

    if not response.status_code != "200":
        raise requests.exceptions.RequestException(
            f"HTTP status code не равен 200: {response.status_code}"
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
        ResponseKeyError: если в ответе ошибка


    """
    if not isinstance(response, dict):
        raise ResponseError(
            "Ответ (response) API должен иметь тип 'dict'"
        )

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
        raise ResponseKeyError(
            "homeworks",
            "В ответе API следующие ключи должны иметь тип 'list'"
        )

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
        raise HomeworkStatusError(
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
    current_timestamp = 0

    while True:
        try:
            response = get_api_answer(current_timestamp)

            homeworks = check_response(response)

            message = "\n\n".join(parse_status(h) for h in homeworks)

        except requests.exceptions.RequestException as err:
            message = f"Недоступен endpoint API yandex.practicum: {err}"
            logger.error(message)

        except BotError as err:
            message = str(err)
            logger.error(message)

        except Exception as err:
            message = f"Сбой в работе программы: {err}"
            logger.error(message)

        # ToDo: сделать кэширование сообщений об ошибках!!
        if not message:
            logger.debug("Статус проверки домашней работы не изменился")
        else:
            send_message(bot, message)

        current_timestamp = int(time.time())

        exit()
        time.sleep(RETRY_TIME)


if __name__ == "__main__":
    main()
