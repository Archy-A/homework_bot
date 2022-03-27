import os
import telegram
import requests
import logging
import time
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
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
    response = requests.get(
        ENDPOINT,
        headers=HEADERS,
        params=params
    )

    if response.status_code == 200:
        logging.debug('Статус не обновлен.')
        return response.json()
    else:
        logging.error(f'Не доступен: {ENDPOINT}.'
                      f'Код ответа API: {response.status_code}.')
        raise Exception('Не корректный status_code.')


def check_response(response):
    """Проверка ответа API."""
    if type(response) == dict:
        response = response.get('homeworks')
        if type(response) == list:
            return response
        logging.error('В словаре нет списка.')
        raise TypeError('Данные не спискок.')
    logging.error('Не корректные данные.')
    raise TypeError('Данные не словарь.')


def parse_status(homework):
    """Статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    for stat in HOMEWORK_STATUSES:
        if stat == homework_status:
            verdict = HOMEWORK_STATUSES[homework_status]
            return (f'Изменился статус проверки работы "{homework_name}".'
                    f'{verdict}')
    logging.error(f'нет такого статуса {homework_status}')
    raise KeyError(f'нет такого статуса {homework_status}')


def check_tokens():
    """Проверка доступности токенов."""
    token_dict = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    for key, token in token_dict.items():
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
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(response['homeworks']) > 0:
                message = parse_status(homework[0])
            else:
                message = 'нет домашки'
            send_message(bot, message)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.error(f'Ошибка: {error}.')
            time.sleep(RETRY_TIME)

if __name__ == '__main__':
    main()
