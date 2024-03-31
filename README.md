# homework_bot
### Описание:
Telegram-бот, который будет обращаться к API сервиса Практикум.Домашка и узнавать статус вашей домашней работы: взята ли ваша домашка в ревью, проверена ли она, а если проверена — то принял её ревьюер или вернул на доработку.
##
### Стек технологий:
<details>
<summary>Подробнее/свернуть</summary>

- Python 3.9.10
- python-telegram-bot
- Pyrogram
</details>

##
### Установка:
<details>
<summary>Подробнее/свернуть</summary>
  
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/veromanich/homework_bot.git
```
```
cd homework_bot
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv env
```
```
source env/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Записать в переменные окружения (файл .env) необходимые ключи:

токен профиля на Яндекс.Практикуме

токен телеграм-бота

свой ID в телеграме

Запустить проект:
```
python homework.py
```
</details>

##
### Автор:
[Роман Веренич](https://github.com/veromanich)
