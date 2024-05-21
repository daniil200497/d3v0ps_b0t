import logging
import paramiko
import time
import re, os
from dotenv import load_dotenv

from telegram import Update, ForceReply, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler

import psycopg2
from psycopg2 import Error

from pathlib import Path

load_dotenv()
TOKEN =    os.getenv('TOKEN')

RM_HOST = os.getenv('RM_HOST')
RM_PORT = os.getenv('RM_PORT')
RM_USER = os.getenv('RM_USER')
RM_PASSWORD = os.getenv('RM_PASSWORD')

DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_DATABASE = os.getenv('DB_DATABASE')



client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


# Подключаем логирование
logging.basicConfig(
    filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

def BigMessage(update: Update, text: str, max_length=4096, delay=0.5):
    parts = [text[i:i+max_length] for i in range(0, len(text), max_length)]
    for part in parts:
        update.message.reply_text(part)
        time.sleep(delay)

def db_request(req):
    connection = None
    res = None

    try:
        connection = psycopg2.connect(user=DB_USER,
                                      password=DB_PASSWORD,
                                      host=DB_HOST,
                                      port=DB_PORT,
                                      database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute(req)
        res = cursor.fetchall()

    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            return res
        return False


def db_insert(req):
    connection = None
    res = None

    try:
        connection = psycopg2.connect(user=DB_USER,
                                      password=DB_PASSWORD,
                                      host=DB_HOST,
                                      port=DB_PORT,
                                      database=DB_DATABASE)

        cursor = connection.cursor()
        cursor.execute(req)
        connection.commit()

    except (Exception, Error) as error:
        logging.error("Ошибка при работе с PostgreSQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            return True


#Начальные команды
def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!\nВведите /get_bot_commands - для справки\n')

def helpCommand(update: Update, context):
    update.message.reply_text("Help!\nВведите /get_bot_commands - для справки\n" )

def getBotComands(update: Update, context):
   msg = "MONITORING:\n" \
         "1.  /get_release\n" \
         "2.  /get_uname\n" \
         "3.  /get_uptime\n" \
         "4.  /get_df\n" \
         "5.  /get_free\n" \
         "6.  /get_mpstat\n" \
         "7.  /get_w\n" \
         "8.  /get_auths\n" \
         "9.  /get_critical\n" \
         "10. /get_ps\n" \
         "11. /get_ss\n" \
         "12. /get_services\n" \
         "13. /get_apt_list\n\n" \
         "  База данных:\n" \
         "14. /get_repl_logs\n" \
         "15. /get_phone_numbers\n" \
         "16. /get_emails\n" \
         "ФУНКЦИИ:\n" \
         "17. /verify_password\n" \
         "18. /findEmail\n" \
         "19. /findPhoneNumbers"
   
   update.message.reply_text(msg)

#Находки
def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров: ')

    return 'findPhoneNumbers'

def findPhoneNumbers(update: Update, context):
    global foundedPhones
    user_input = update.message.text

    phoneNumRegexs = [
        re.compile(r'8 \(\d{3}\) \d{3}-\d{2}-\d{2}'),    # формат 8 (000) 000-00-00
        re.compile(r'\+7 \(\d{3}\) \d{3}-\d{2}-\d{2}'),  # формат +7 (000) 000-00-00
        re.compile(r'8\d{10}'),                          # формат 80000000000
        re.compile(r'\+7\d{10}'),                        # формат +70000000000
        re.compile(r'8\(\d{3}\)\d{7}'),                  # формат 8(000)0000000
        re.compile(r'\+7\(\d{3}\)\d{7}'),                # формат +7(000)0000000
        re.compile(r'8 \d{3} \d{3} \d{2} \d{2}'),        # формат 8 000 000 00 00
        re.compile(r'\+7 \d{3} \d{3} \d{2} \d{2}'),      # формат +7 000 000 00 00
        re.compile(r'8 \(\d{3}\) \d{3} \d{2} \d{2}'),    # формат 8 (000) 000 00 00
        re.compile(r'\+7 \(\d{3}\) \d{3} \d{2} \d{2}'),  # формат +7 (000) 000 00 00
        re.compile(r'8-\d{3}-\d{3}-\d{2}-\d{2}'),        # формат 8-000-000-00-00
        re.compile(r'\+7-\d{3}-\d{3}-\d{2}-\d{2}')       # формат +7-000-000-00-00
    ]

    phoneNumberList = [] # Ищем номера телефонов
    for i in phoneNumRegexs:
        phoneNumberList.extend(i.findall(user_input))
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены!\nВведите /get_bot_commands - для справки')
        return ConversationHandler.END

    phoneNumbers = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{i+1}. {phoneNumberList[i]}\n'

    update.message.reply_text(phoneNumbers)
    foundedPhones = phoneNumberList
    update.message.reply_text("Сохранить найденные номера в базу ? Напишите 'yes', чтобы сохранить")

    return 'add_Phone_number'

def add_Phone_number(update: Update, context):
    user_input = update.message.text
    if user_input == 'yes':
        res = ''
        for i in foundedPhones:
            res += "('" + i + "')" + ','
        res = res[:-1:]

        if db_insert('INSERT INTO phone_data (phone_number) values ' + res + ';'):
            update.message.reply_text("Номера телефонов сохранены!\nВведите /get_bot_commands - для справки")
        else: update.message.reply_text("ERROR Номера телефонов  НЕ сохранены!\nВведите /get_bot_commands - для справки")
    else:
        update.message.reply_text("Данные не сохранены!\nВведите /get_bot_commands - для справки")

    return ConversationHandler.END

def findEmailCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска адреса почты: ')

    return 'findEmail'

def findEmail(update: Update, context):
    global foundedEmails

    user_input = update.message.text

    emailRegex = re.compile(r'\b[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+(?:\.[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+)*' \
                            r'@(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b')

    emailList = emailRegex.findall(user_input)
    if not emailList:
        update.message.reply_text('Email-адреса не найдены\nВведите /get_bot_commands - для справки')
        return ConversationHandler.END

    email = ''
    for i in range(len(emailList)):
        email += f'{i+1}. {emailList[i]}\n'

    update.message.reply_text(email)
    foundedEmails = emailList
    update.message.reply_text("Сохранить найденные адреса в базу ? Напишите 'yes', чтобы сохранить")

    return 'add_Email'

def add_Email(update: Update, context):
    user_input = update.message.text
    if user_input == 'yes':
        res = ''
        for i in foundedEmails:
            res += "('" + i +"')" + ','
        res = res[:-1:]

        if db_insert('insert into email_data (email) values ' + res + ';'):
            update.message.reply_text("Email-адреса сохранены!\nВведите /get_bot_commands - для справки")
        else: update.message.reply_text("ERROR Email-адреса не сохранены!\nВведите /get_bot_commands - для справки")
    else:
        update.message.reply_text("Email-адреса не сохранены\nВведите /get_bot_commands - для справки")

    return ConversationHandler.END

def get_emails(update: Update, context):
    res = db_request("SELECT * FROM email_data;")
    for row in res:
        update.message.reply_text(row)

def get_phone_numbers(update: Update, context):
    res = db_request("SELECT * FROM phone_data;")
    for row in res:
        update.message.reply_text(row)

#Проверялки
def verify_password_command(update: Update, context):
    update.message.reply_text('Введите текст проверки пароля: ')

    return 'verify_password'

def verify_password(update: Update, context):
    user_input = update.message.text

    regExps = [
        re.compile(r'\S{8,}'),
        re.compile(r'[A-Z]'),
        re.compile(r'[a-z]'),
        re.compile(r'\d'),
        re.compile(r'[\!\@\#\$\%\^\&\*\(\)\.]')
    ]
    for i in regExps:
        if not i.search(user_input):
            update.message.reply_text('Пароль простой\nВведите /get_bot_commands - для справки')
            return ConversationHandler.END
    update.message.reply_text('Пароль сложный\nВведите /get_bot_commands - для справки')
    return ConversationHandler.END





#ПОВТОРЮШКА
def echo(update: Update, context):
    update.message.reply_text(update.message.text)



# Блоки создаем 
def get_release(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('lsb_release -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_uname(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('uname -a')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_uptime(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('uptime')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_df(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('df -h')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_free(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('free -m')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_mpstat(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_w(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_auths(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('last -10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_critical(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('journalctl -p err -b -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_ps(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('ps aux | head -n 10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_ss(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('ss -tuln')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

#def get_apt_list(update: Update, context):
    command = 'apt list '
    args = update.message.text.split(' ')[1::]
    for arg in args:
        command += arg
        command += ' '

    client.connect(hostname=RM_HOST, username=username, password=password, port=port)
    stdin, stdout, stderr = client.exec_command(command + ' | head -n10')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_apt(update, context):
    reply_markup = ReplyKeyboardMarkup([['Все пакеты', 'Один пакет']], one_time_keyboard=True)
    update.message.reply_text('Выберите, какую информацию вы хотите получить:', reply_markup=reply_markup)
    return 'choose_option'

def choose_option(update, context):
    option = update.message.text
    if option == 'Все пакеты':
        command = 'dpkg -l | head -n 10'
        client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
        stdin, stdout, stderr = client.exec_command(command)
        data = stdout.read().decode('utf-8')
        client.close()
        update.message.reply_text(data, reply_markup=ReplyKeyboardRemove())
    elif option == 'Один пакет':
        update.message.reply_text('Введите название пакета:')
        return 'get_specific_package'
    else:
        update.message.reply('Пожалуйста, выберите один из вариантов: "Все пакеты" или "Один пакет"')
    return ConversationHandler.END

def get_specific_package(update, context):
    package_name = update.message.text
    command = f'dpkg -l | grep {package_name}'
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command(command)
    data = stdout.read().decode('utf-8')
    client.close()
    update.message.reply_text(data, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def get_services(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command('systemctl list-units --type=service | head -n 10')
    
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

#DB
def get_repl_logs(update: Update, context):
    log_dir = Path('/app/logs')
    log_file_path = log_dir / 'postgresql.log'

    try:
        if log_file_path.exists():
            res = ""
            with open(log_file_path, 'r', encoding='utf-8') as file:
                
                for line in file:
                    lowerLine = line.casefold()
                    if ('repl' in lowerLine) or ('репл' in lowerLine):
                        res += line.rstrip() + "\n"

            if res:
                BigMessage(update, res)
            else:
                update.message.reply_text("No logs\nВведите /get_bot_commands - для справки")
                logging.info("No logs\nВведите /get_bot_commands - для справки")
        else:
            update.message.reply_text("File for log didn't find\nВведите /get_bot_commands - для справки")
            logging.error("File for log didn't find\nВведите /get_bot_commands - для справки")
    except Exception as e:
        update.message.reply_text(f"Error log: {str(e)}")
        logging.error(f"Error log: {str(e)}")


#def get_email_data(update: Update, context):
    client.connect(hostname=RM_HOST, username=RM_USER, password=RM_PASSWORD, port=RM_PORT)
    stdin, stdout, stderr = client.exec_command(f"psql -d {email_phone_database} -c \"SELECT * FROM email_data\"")
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

#def get_phone_data(update: Update, context):
    client.connect(hostname=host, username=username_postgres, password=password_postgres, port=port)
    stdin, stdout, stderr = client.exec_command(f"psql -d {email_phone_database} -c \"SELECT * FROM phone_data\"")
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END


def main():
    updater = Updater(TOKEN, use_context=True)

    # Получаем диспетчер для регистрации обработчиков
    dp = updater.dispatcher


    # Обработчик диалога
    convHandlerFindPhoneNumbers = ConversationHandler(
        entry_points=[CommandHandler('findPhoneNumbers', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'add_Phone_number': [MessageHandler(Filters.text & ~Filters.command, add_Phone_number)],
        },
        fallbacks=[]
    )
    convHandlerFindEmail = ConversationHandler(
        entry_points=[CommandHandler('findEmail', findEmailCommand)],
        states={
            'findEmail': [MessageHandler(Filters.text & ~Filters.command, findEmail)],
            'add_Email': [MessageHandler(Filters.text & ~Filters.command, add_Email)],
        },
        fallbacks=[]
    )
    convHandlerCheckPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verify_password_command)],
        states={
            'verify_password': [MessageHandler(Filters.text & ~Filters.command, verify_password)],
        },
        fallbacks=[]
    )
    conv_handler_get_apt = ConversationHandler(
    entry_points=[CommandHandler('get_apt_list', get_apt)],
    states={
        'choose_option': [MessageHandler(Filters.regex('^(Все пакеты|Один пакет)$'), choose_option)],
        'get_specific_package': [MessageHandler(Filters.text & ~Filters.command, get_specific_package)],
    },
    fallbacks=[]
)

    # Регистрируем обработчики команд
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))
    dp.add_handler(CommandHandler("get_bot_commands", getBotComands))
    
    #MONITORING
    dp.add_handler(CommandHandler("get_release", get_release))
    dp.add_handler(CommandHandler("get_uname", get_uname))
    dp.add_handler(CommandHandler("get_uptime", get_uptime))
    dp.add_handler(CommandHandler("get_df", get_df))
    dp.add_handler(CommandHandler("get_free", get_free))
    dp.add_handler(CommandHandler("get_mpstat", get_mpstat))
    dp.add_handler(CommandHandler("get_w", get_w))
    dp.add_handler(CommandHandler("get_auths", get_auths))
    dp.add_handler(CommandHandler("get_critical", get_critical))
    dp.add_handler(CommandHandler("get_ps", get_ps))
    dp.add_handler(CommandHandler("get_ss", get_ss))
    dp.add_handler(CommandHandler("get_services", get_services))
    #DB
    dp.add_handler(CommandHandler("get_repl_logs", get_repl_logs))
    dp.add_handler(CommandHandler("get_phone_numbers", get_phone_numbers))
    dp.add_handler(CommandHandler("get_emails", get_emails))


    #dp.add_handler(CommandHandler("get_emails", get_email_data))
    #dp.add_handler(CommandHandler("get_phone_numbers", get_phone_data))
    

    dp.add_handler(convHandlerFindPhoneNumbers)
    dp.add_handler(convHandlerFindEmail)
    dp.add_handler(convHandlerCheckPassword)
    dp.add_handler(conv_handler_get_apt)

    # Регистрируем обработчик текстовых сообщений
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))


    # Запускаем бота
    updater.start_polling()


    # Останавливаем бота при нажатии Ctrl+C
    updater.idle()


if __name__ == '__main__':
    main()
