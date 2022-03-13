import zipfile
import os
from os import path
import shutil
from PyPDF2 import PdfFileReader, PdfFileWriter

import telebot
import config


bot = telebot.TeleBot(config.TOKEN)
programmPath = '/home/shah484/Downloads/splitter/'


def split_pdf(fileName):
    pdf = PdfFileReader(fileName)
    docName = fileName[:-4]


    pagesPath = '{}{}-splitted'.format(programmPath, docName)
    print('PAGES PATH ==== ' + pagesPath)

    try:
        os.mkdir(pagesPath)
    except OSError:
        print('Создать директорию не удалось')
    else:
        print('Директория создана')

    for page in range(pdf.getNumPages()):
        pdf_writer = PdfFileWriter()
        current_page = pdf.getPage(page)
        pdf_writer.addPage(current_page)

        outputFilename = '{}/{}-page-{}.pdf'.format(pagesPath, docName, page + 1)
        with open(outputFilename, 'wb') as out:
            pdf_writer.write(out)

            print('created', outputFilename)



@ bot.message_handler(content_types=['text'])
def get_text_message(message):
    msgText = str(message.text)
    chatId = message.chat.id


@ bot.message_handler(content_types=['document'])
def get_document_message(message):
    chatId = message.chat.id

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    fileName = message.document.file_name
    with open(fileName , 'wb') as new_file:
        new_file.write(downloaded_file)

    if fileName.endswith('.pdf'):
        docName = fileName[:-4]
        print('document ==== ' + docName)
        split_pdf(fileName)
        pagesPath = '{}{}-splitted'.format(programmPath, docName)
        zipFilePath = pagesPath + '.zip'
        # archive_name, format, root_dir
        #shutil.make_archive(zipFilePath, 'zip', pagesPath)
        bot.send_chat_action(chatId, 'upload_document')
        with zipfile.ZipFile(zipFilePath, 'w') as myzip:
            myzip.write(zipFilePath)
        with open(zipFilePath, 'rb') as fileToSend:
            bot.send_document(chatId, zipFilePath)
        #with open('{}{}-splitted.zip'.format(programmPath, document[:-4]), encoding='utf-16') as file:
        #   bot.send_document(chatId, file)
#        f = codecs.open('{}{}-splitted.zip'.format(programmPath, document[:-4]))
#        ff = f.read()
#        f.write(ff.encode('utf-8'))
        #with open('{}{}-splitted.zip'.format(programmPath, document[:-4])) as fileToSend:
        #    bot.send_document(chatId, fileToSend)
        #bot.send_document(chatId, open('{}{}-splitted.zip'.format(programmPath, document[:-4])))


bot.polling(none_stop=True, interval=0)