import os
import time
import config
import shutil
import logging
import psycopg2
from os import path
from pydoc import doc
from fileinput import filename
from distutils.dir_util import remove_tree
from PyPDF2 import PdfFileReader, PdfFileWriter
from telegram import ChatAction, ForceReply, Update, ForceReply
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext




# Database connection
conn = psycopg2.connect(
    dbname=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host='0.0.0.0')  
cursor = conn.cursor()

# Logger settings
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='info.log'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TYPING_SLEEPTIME = 1


def splitPdf(fileName) -> str:
    pdfFile = PdfFileReader('./data/{}'.format(fileName))
    # Remove a file extension from it`s name
    docName = fileName[:-4]

    pagesFolder = '{}-splitted'.format(docName)
    os.mkdir('./data/{}'.format(pagesFolder))
    
    for page in range(pdfFile.getNumPages()):
        pdfWriter = PdfFileWriter()
        currentPage = pdfFile.getPage(page)
        pdfWriter.addPage(currentPage)

        pageFileName = './data/{}/{}-page-{}.pdf'.format(pagesFolder, docName, page + 1)
        
        with open(pageFileName, 'wb') as out:
            pdfWriter.write(out)
    return pagesFolder


def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    update.message.reply_markdown_v2(
        'Привет, {}\!\n\nЯ разделяю PDF файлы на странички, пакую странички в отдельные PDF файлы и собираю их в архив\nПришли мне PDF файл, а я разделю его по страницам и верну тебе ZIP архив'.format(user.first_name)
    )
    
    cursor.execute('SELECT insert_user({});'.format(update.effective_user.id))
    conn.commit()

    logger.info('User "{}" start using bot'.format(update.effective_user.username))

def help(update: Update, context: CallbackContext) -> None:
    update.message.chat.send_action(ChatAction.TYPING)
    time.sleep(TYPING_SLEEPTIME)
    update.message.reply_text(
        'Просто пришли мне файл формата PDF!\nЯ разделю его на страницы, запакую и отправлю тебе архив со страницами в виде PDF файлов'
    )


def processPdfFile(update: Update, context: CallbackContext) -> None:
    fileName = update.message.document.file_name
    # Create file and write the PDF data to it
    open('./data/{}'.format(fileName), 'a').close()
    update.message.document.get_file().download('./data/{}'.format(fileName))

    pagesFolder = splitPdf(fileName)
    zipPath = './data/{}.zip'.format(pagesFolder)
    shutil.make_archive('./data/{}'.format(pagesFolder), 'zip', './data/{}'.format(pagesFolder))

    with open(zipPath, 'rb') as fileToSend:
        update.message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)
        update.message.reply_document(zipPath)
    
    cursor.execute('SELECT insert_request({});'.format(update.effective_user.id))
    conn.commit()
    
    # Remove processed files
    os.remove(zipPath)
    os.remove('./data/{}'.format(fileName))
    shutil.rmtree('./data/{}'.format(pagesFolder))

    logger.info('User "{}" split file'.format(update.effective_user.username))


def nonPdfFileAlert(update: Update, context: CallbackContext) -> None:
    update.message.chat.send_action(ChatAction.TYPING)
    time.sleep(TYPING_SLEEPTIME)
    update.message.reply_text("Мне не подходит файл такого формата, я принимаю только PDF")

def textAlert(update: Update, context: CallbackContext) -> None:
    update.message.chat.send_action(ChatAction.TYPING)
    time.sleep(TYPING_SLEEPTIME)
    update.message.reply_text("Я пока не умею поддерживать разговор, пришли мне PDF файл")


def main() -> None:
    # Start the bot on local server
    updater = Updater(config.TOKEN, base_url="http://0.0.0.0:8081/bot")
    dispatcher = updater.dispatcher
    
    # Create folder for processed files
    if not os.path.exists('data'):
        os.mkdir('data')

    # Create handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(MessageHandler(Filters.text, textAlert))
    dispatcher.add_handler(MessageHandler(Filters.document & ~Filters.document.pdf, nonPdfFileAlert))
    dispatcher.add_handler(MessageHandler(Filters.document.pdf, processPdfFile))

    updater.start_polling()


if __name__ == '__main__':
    main()
