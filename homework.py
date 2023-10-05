import logging
import os
import time
from http import HTTPStatus
from os.path import abspath, dirname

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (
    EmptyResponseApiException,
    EnvironmentVariableError,
    StatusCodeException,
)


load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

LOG_PATH = dirname(abspath(__name__))

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(f'{LOG_PATH}/my_logger.log')
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s, '
    '%(module)s, %(lineno)d, %(funcName)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens():
    """Check the availability of environment variables."""
    environment_variables = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
    }
    if not all([variable for variable in environment_variables.values()]):
        missing_variables = []
        for name, variable in environment_variables.items():
            if variable is None:
                missing_variables.append(name)
        if missing_variables:
            logger.critical(
                'Отсутствуют обязательные переменные окружения: '
                f'{", ".join(missing_variables)}'
            )
            raise EnvironmentVariableError(
                'Отсутствуют обязательные переменные окружения: '
                f'{", ".join(missing_variables)}'
            )
    logger.info('Все обязательные переменные окружения заданы.')


def send_message(bot, message):
    """Send a message to Telegram chat."""
    try:
        logger.info(f'Начало отправки сообщения "{message}"')
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug(f'Бот отправил сообщение "{message}"')
    except telegram.error.TelegramError as error:
        logger.error(f'Ошибка отправки сообщения: {error}')


def get_api_answer(timestamp):
    """Make a request to the API service endpoint."""
    request_parameters = {
        'endpoint': ENDPOINT,
        'headers': HEADERS,
        'params': {'from_date': timestamp},
    }
    try:
        logger.info(
            'Программа начала запрос: '
            f'адрес - {request_parameters["endpoint"]}, '
            f'заголовок - {request_parameters["headers"]}, '
            f'параметры - {request_parameters["params"]}'
        )
        response = requests.get(
            request_parameters['endpoint'],
            headers=request_parameters['headers'],
            params=request_parameters['params'],
        )
    except requests.RequestException as error:
        raise error(
            'Сбой в работе: '
            f'Эндпоинт {request_parameters["endpoint"]} недоступен'
        )
    if response.status_code != HTTPStatus.OK:
        raise StatusCodeException('Status code отличный от "200"')
    return response.json()


def check_response(response):
    """Check the API response for consistency."""
    request_errors = {
        'UnknownError': 'Неверный формат from_date',
        'not_authenticated': 'Учетные данные не были предоставлены.',
    }
    if not isinstance(response, dict):
        raise TypeError('Ожидается словарь')
    if 'homeworks' not in response:
        raise EmptyResponseApiException(
            f'Ответ API: {request_errors[response["code"]]}'
        )
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Ожидается список')
    logger.info('Ответ API соответствует ожидаемому')
    return homeworks


def parse_status(homework):
    """Retrieve the homework status."""
    try:
        homework_name = homework['homework_name']
    except KeyError:
        raise KeyError('Ключ "homework_name" не найден')
    if homework['status'] in HOMEWORK_VERDICTS:
        verdict = HOMEWORK_VERDICTS[homework['status']]
        logger.info(
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    logger.error(f'Неожиданный статус проверки работы "{homework_name}"')
    raise ValueError(f'Неожиданный статус проверки работы "{homework_name}"')


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    current_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                new_message = parse_status(homeworks[0])
            else:
                new_message = 'Отсутствие в ответе новых статусов'
                logger.debug('Отсутствие в ответе новых статусов')
            if new_message != current_message:
                send_message(bot, new_message)
                current_message = new_message
        except EmptyResponseApiException:
            logger.error('Ответ API - пустой список')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if current_message != message:
                send_message(bot, message)
                current_message = message
        finally:
            timestamp = response.get('current_date', timestamp)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s, %(levelname)s, %(message)s, '
            '%(module)s, %(lineno)d, %(funcName)s'
        ),
    )

    main()
