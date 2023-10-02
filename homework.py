import logging
import os
import time

import requests
import telegram

from dotenv import load_dotenv


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s',
)

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()


class StatusCodeException(Exception):
    """Status code other than 200."""

    pass


class ListEmpty(Exception):
    """Empty list."""

    pass


def check_tokens():
    """Checks the availability of environment variables."""
    environment_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    if all([variable for variable in environment_variables.values()]):
        logger.info('Все обязательные переменные окружения заданы.')
        return True
    else:
        for name, variable in environment_variables.items():
            if variable is None:
                logger.critical(
                    f'Отсутствует обязательная переменная окружения: {name}'
                )
        return False


def send_message(bot, message):
    """Sends a message to Telegram chat."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug(f'Бот отправил сообщение "{message}"')
    except Exception as error:
        logging.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Makes a request to the API service endpoint."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except Exception as error:
        logging.error(
            f'Сбой в работе: Эндпоинт {ENDPOINT} недоступен. {error}'
        )
    if response.status_code != 200:
        raise StatusCodeException('Status code отличный от "200"')
    return response.json()


def check_response(response):
    """Checks the API response for consistency."""
    request_errors = {
        'UnknownError': 'Неверный формат from_date',
        'not_authenticated': 'Учетные данные не были предоставлены.',
    }
    if type(response) != dict:
        logging.error('Тип ответа API не соответствует ожидаемому')
        raise TypeError('Ожидается словарь')
    elif 'homeworks' not in response:
        logging.error(f'Ответ API: {request_errors[response["code"]]}')
        logging.error('В ответе API нет ключа "homeworks"')
        raise KeyError('Нет ключа "homeworks"')
    elif type(response['homeworks']) != list:
        logging.error('Тип ответа API не соответствует ожидаемому')
        raise TypeError('Ожидается список')
    elif 'code' in response:
        logging.error(f'Ответ API: {request_errors[response["code"]]}')
        return False
    elif len(response['homeworks']) == 0:
        logging.debug('Нет новых домашних работ')
        raise ListEmpty('Нет новых домашних работ')
    logging.info('Ответ API соответствует ожидаемому')
    return True


def parse_status(homework):
    """Retrieves the homework status."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        logging.error('Ключ "homework_name" не найден')
        raise KeyError('Ключ "homework_name" не найден')
    if homework['status'] in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework['status']]
        logging.info(
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    else:
        logging.error(f'Неожиданный статус проверки работы "{homework_name}"')
        raise ValueError(
            f'Неожиданный статус проверки работы "{homework_name}"'
        )


def main():
    """Основная логика работы бота."""
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        timestamp = int(time.time())
        current_message = ''
        while True:
            try:
                response = get_api_answer(timestamp)
                if check_response(response):
                    new_message = parse_status(response['homeworks'][0])
                    if new_message != current_message:
                        send_message(bot, new_message)
                        current_message = new_message
                    else:
                        logging.debug('Отсутствие в ответе новых статусов')
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logging.error(message)
                send_message(bot, message)
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
