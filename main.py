"""AI Talent Hub telegram bot"""

import os
import time
from datetime import datetime
from threading import Thread

import psycopg2
import telebot
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv
from telebot import types


load_dotenv()

poll_link = os.getenv('poll_link')
chat_link = os.getenv('chat_link')
feedback_link = os.getenv('feedback_link')
admin_id = int(os.getenv('admin_id'))
token = os.getenv('tg_token')

scheduler = BlockingScheduler(timezone='Europe/Moscow')

bot = telebot.TeleBot(token)


with open('texts/feedback.txt', 'r') as f:
    feedback_text = f.read()

with open('texts/reminder.txt', 'r') as f:
    reminder_text = f.read()

with open('texts/start.txt', 'r') as f:
    start_text = f.read()

with open('texts/poll.txt', 'r') as f:
    poll_text = f.read()

with open('texts/admin_feedback.txt', 'r') as f:
    admin_feedback_text = f.read()

with open('texts/connect.txt', 'r') as f:
    connect_text = f.read()


def get_db_connection():
    """
    Соединение с бд
    """
    conn = psycopg2.connect(
        host=os.getenv("host"),
        dbname=os.getenv("db"),
        user=os.getenv("user"),
        password=os.getenv("password"),
        port=os.getenv("port"),
    )

    return conn


def send_schedule():
    """
    Запланированная отправка расписания
    """
    day = datetime.now()
    name = str(day.date())
    path = os.path.join('schedules', name + '.png')
    if os.path.exists(path):
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            select_ids = """
            SELECT DISTINCT tg_id
            FROM tg_ids;
            """
            cur.execute(select_ids)
            id_list = cur.fetchall()

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        date = name.split('-')
        date = '/'.join([date[2], date[1]])
        to_send = f'Расписание на {date}'
        for id in id_list:
            try:
                bot.send_photo(
                    id[0],
                    photo=open(path, 'rb'),
                    caption=to_send
                    )
            except Exception as e:
                print(f'Error sending, id: {id[0]}, error: {e}')


def send_feedback():
    """
    Запланированная отправка формы для обратной связи
    """
    day = datetime.now()
    date = str(day.date())
    # отправка ссылки на форму происходит только во время кэмпа
    if date in ['2023-06-29', '2023-06-30']:
        markup = types.InlineKeyboardMarkup()
        option_1 = types.InlineKeyboardButton(
            text='Обратная связь',
            url=feedback_link
            )
        markup.add(option_1)
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            select_ids = """
            SELECT DISTINCT tg_id
            FROM tg_ids;
            """
            cur.execute(select_ids)
            id_list = cur.fetchall()

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        for id in id_list:
            try:
                bot.send_message(
                    id[0],
                    text=feedback_text,
                    reply_markup=markup
                    )
            except Exception as e:
                print(f'Error sending, id: {id[0]}, error: {e}')


def send_reminder_notificaton():
    """
    Запланированное напоминание перед началом дня
    """
    day = datetime.now()
    date = str(day.date())
    # отправка напоминания происходит только во время кэмпа
    if date in ['2023-06-29', '2023-06-30']:
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            select_ids = """
            SELECT DISTINCT tg_id
            FROM tg_ids;
            """
            cur.execute(select_ids)
            id_list = cur.fetchall()

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        for id in id_list:
            try:
                bot.send_message(
                    id[0],
                    text=reminder_text,
                    parse_mode='html'
                    )
            except Exception as e:
                print(f'Error sending, id: {id[0]}, error: {e}')


def scheduler_checker():
    """
    Отслеживание задач
    """
    while True:
        scheduler.start()


@bot.message_handler(commands=['start'])
def start(message):
    """
    Приветственная фраза и меню
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       row_width=1
                                       )

    option_1 = types.KeyboardButton('Подключиться к встрече 📞')
    option_2 = types.KeyboardButton('Дать обратную связь 📣')
    markup.add(option_1, option_2)

    bot.send_message(
        message.chat.id,
        text=start_text,
        reply_markup=markup,
        parse_mode='html'
        )

    # сохранение id в бд
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        add_id = """
        INSERT INTO tg_ids (tg_id)
        VALUES (%s);
        """
        cur.execute(add_id, (message.chat.id,))
        conn.commit()

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    time.sleep(1)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text='Хочу выбрать темы!', url=poll_link)
    )

    bot.send_message(
        message.chat.id,
        text=poll_text,
        reply_markup=markup
        )


@bot.message_handler(commands=['admin_send_schedule'])
def admin_send_schedule(message):
    """
    Высылает расписание по триггеру от админа
    """
    if message.chat.id == admin_id:
        day = datetime.now()
        name = str(day.date())
        path = os.path.join('schedules', name + '.png')
        if os.path.exists(path):
            conn = None
            cur = None
            try:
                conn = get_db_connection()
                cur = conn.cursor()
                select_ids = """
                SELECT DISTINCT tg_id
                FROM tg_ids;
                """
                cur.execute(select_ids)
                id_list = cur.fetchall()

            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.close()

            date = name.split('-')
            date = '/'.join([date[2], date[1]])
            to_send = f'Актуальное расписание на {date}'
            for id in id_list:
                try:
                    bot.send_photo(
                        id[0],
                        photo=open(path, 'rb'),
                        caption=to_send
                        )
                except Exception as e:
                    print(f'Error sending, id: {id[0]}, error: {e}')


@bot.message_handler(commands=['admin_send_feedback'])
def admin_send_feedback(message):
    """
    Высылает форму для обратной связи по триггеру от админа
    """
    if message.chat.id == admin_id:
        markup = types.InlineKeyboardMarkup()
        option_1 = types.InlineKeyboardButton(
            text='Обратная связь',
            url=feedback_link
            )
        markup.add(option_1)
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            select_ids = """
            SELECT DISTINCT tg_id
            FROM tg_ids;
            """
            cur.execute(select_ids)
            id_list = cur.fetchall()

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        for id in id_list:
            try:
                bot.send_message(
                    id[0],
                    text=admin_feedback_text,
                    reply_markup=markup
                    )
            except Exception as e:
                print(f'Error sending, id: {id[0]}, error: {e}')


@bot.message_handler(commands=['admin_send_both'])
def admin_send_both(message):
    """
    Высылает расписание обоих дней всем пользователям
    """
    path_1 = 'schedules/2023-06-29.png'
    path_2 = 'schedules/2023-06-30.png'
    if ((message.chat.id == admin_id) and
            os.path.exists(path_1) and
            os.path.exists(path_2)):
        to_send = 'Ура! Самые горячие темы собраны. Скорее смотри расписание нашего кэмпа 😎'
        conn = None
        cur = None
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            select_ids = """
            SELECT DISTINCT tg_id
            FROM tg_ids;
            """
            cur.execute(select_ids)
            id_list = cur.fetchall()

        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

        for id in id_list:
            try:
                bot.send_media_group(id[0],
                             [types.InputMediaPhoto(open(path_1, 'rb'), caption=to_send),
                              types.InputMediaPhoto(open(path_2, 'rb'))
                              ]
                            )
            except Exception as e:
                print(f'Error sending, id: {id[0]}, error: {e}')


@bot.message_handler(content_types=['text'])
def get_user_text(message):
    """
    Обработка текстовых сообщений из кнопок меню
    """
    if message.text == 'Подключиться к встрече 📞':
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text='Подключение', url=chat_link)
        )

        bot.send_message(
            message.chat.id,
            text=connect_text,
            reply_markup=markup,
            parse_mode='html'
        )

    elif message.text == 'Дать обратную связь 📣':
        to_send = 'Оставить обратную связь можно по ссылке ниже 👇'
        markup = types.InlineKeyboardMarkup()
        option_1 = types.InlineKeyboardButton(
            text='Обратная связь',
            url=feedback_link
            )
        markup.add(option_1)

        bot.send_message(
            message.chat.id,
            text=to_send,
            reply_markup=markup
        )

    else:
        to_send = 'Пожалуйста, используйте команды меню. Спасибо!'
        bot.send_message(
            message.chat.id,
            text=to_send
        )


if __name__ == '__main__':
    # добавляем задачи
    scheduler.add_job(send_schedule, 'cron', hour=12)
    scheduler.add_job(send_feedback, 'cron', hour=20, minute=5)
    scheduler.add_job(send_reminder_notificaton, 'cron', hour=15, minute=55)

    Thread(target=scheduler_checker).start()
    bot.infinity_polling()
