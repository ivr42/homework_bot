# homework_bot

Телеграм-бот, проверяет статус выполнения домашнего задания в системе Yandex 
Practicum. Результат отправляется по указанному `chat_id`.

## Стек технологий, использованных в проекте
- Python 3.9.13
- [python-telegram-bot 13.7](https://python-telegram-bot.org/)
- requests

## Установка
1. Клонировать репозиторий и перейти в него в командной строке:
```shell
git clone https://github.com/ivr42/api_final_yatube
```

```shell
cd api_final_yatube
```

2. Cоздать и активировать виртуальное окружение:
```shell
python3 -m venv venv
source venv/bin/activate
```

3. Установить зависимости из файла requirements.txt:
```shell
python3 -m pip install --upgrade pip
pip install -r requirements.txt
```

## Environment variables

 - `PRACTICUM_TOKEN` — Яндекс Практикум API token
 - `TELEGRAM_TOKEN`
 - `TELEGRAM_CHAT_ID`


## API Яндекс Практикум
Для взаимодействия с API Яндекс Практикум используются следующие ресуры:

#### Endpoint
https://practicum.yandex.ru/api/user_api/homework_statuses/

#### Enroll token
https://oauth.yandex.ru/authorize?response_type=token&client_id=1d0b9dd4d652455a9eb710d450ff456a

