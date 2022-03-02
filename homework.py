import os
import logging
import telegram
import time
import requests
from dotenv import load_dotenv
from http import HTTPStatus


load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')


RETRY_TIME = 600


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        return bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Делает запрос к API сервиса."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
    headers = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
    homework_statuses = requests.get(ENDPOINT, headers=headers, params=params)
    if homework_statuses.status_code == HTTPStatus.OK:
        return homework_statuses.json()
    else:
        logging.error('Не удалось проверить статус задания')
        raise Exception


def check_response(response):
    """Проверяет ответ API на корректность."""
    homework = response['homeworks']
    if type(homework) is not list:
        logging.error('Ответ приходят не в виде списка')
    else:
        return homework


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        logging.error('В ответе API не содержится ключ homework_name.')
    homework_status = homework.get('status')
    if 'status' not in homework:
        logging.error('В ответе API не содержится ключ status.')
    if homework_status not in HOMEWORK_STATUSES.keys():
        logging.error(f'Статус домашней работы {homework_status} некорректен.')
    verdict = HOMEWORK_STATUSES[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}". {verdict}'
    return message


def check_tokens():
    """Проверяем доступность переменных окружения."""
    if (PRACTICUM_TOKEN is None
       and TELEGRAM_TOKEN is None
       and TELEGRAM_CHAT_ID is None):
        logging.error('Отсутствует хотя бы одна переменная окружения')
        return False
    return True


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            text = parse_status(response.get('homeworks')[0])
            if response.get('homeworks'):
                bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=text)
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
