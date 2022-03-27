import os
import telegram
import requests
import logging
import time
from dotenv import load_dotenv

load_dotenv()


TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_RETRY_TIME = 600

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправление сообщения в телеграмм."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.info('Сообщение отправлено!')
    except Exception as error:
        logging.error(f'Ошибка : {error}.')


def get_api_answer(current_timestamp):
    """Запрос к API сервису."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
    except requests.RequestException as error:
        logging.error(f'Ошибка на сервере: {error}.')
    if response.status_code != 200:
        logging.error(f'Не доступен: {ENDPOINT}.'
                      f'Код ответа API: {response.status_code}.')
        raise Exception('Не корректный status_code.')
    logging.debug('status_code доступен.')
    return response.json()


def check_response(response):
    """Проверка ответа API."""
    if not isinstance(response, dict):
        logging.error('Не корректные данные.')
        raise TypeError('Данные не словарь.')
    if 'homeworks' not in response.keys():
        logging.error('нет homeworks в словаре.')
        raise TypeError('нет homeworks в словаре.')
    response = response.get('homeworks')
    if not isinstance(response, list):
        logging.error('В словаре нет списка.')
        raise TypeError('Данные не спискок.')
    return response


def parse_status(homework):
    """Статус домашней работы."""
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'нет такого статуса {homework_status}')
    homework_name = homework['homework_name']
    verdict = HOMEWORK_STATUSES[homework_status]
    return (f'Изменился статус проверки работы "{homework_name}".'
            f'{verdict}')


def check_tokens():
    """Проверка доступности токенов."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for key, token in tokens.items():
        if token is None:
            logging.critical(f'Отсутствует переменная окружения:'
                             f'{key}. Ошибка.')
            return False
    return True


def main():
    """Основная функция бота."""
    while check_tokens() is True:
        try:
            bot = telegram.Bot(token=TELEGRAM_TOKEN)
            current_timestamp = int(time.time())
            res = get_api_answer(current_timestamp)
            s_res = check_response(res)
            message = parse_status(s_res[0]) if len(res['homeworks']) \
                                             > 0 else 'нет домашки'
            send_message(bot, message)
            current_timestamp = res.get('current_date')
        except Exception as error:
            logging.exception(f'Ошибка: {error}.')
        finally:
            time.sleep(TELEGRAM_RETRY_TIME)


if __name__ == '__main__':
    main()
