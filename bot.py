import logging
from flask import Flask, request
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, Dispatcher
from telegram.ext import CallbackQueryHandler, ConversationHandler, CallbackContext
from telegram import Bot, Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from convohandler import courses, admin, cs, ce, me, ee
from utils import get_reply
from firebaseutils import answers_collection
from location import suggest_path
import speech_recognition as sr
import os
import numpy as np
from stackapi import StackAPI
from dotenv import load_dotenv
load_dotenv()

#enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)
logger = logging.getLogger(__name__)

# Stages
FIRST, SECOND = range(2)
# Callback data
ONE, TWO, THREE, FOUR = range(4)

#Telegram Bot Token
#TOKEN = "1474907865:AAGqLgIV9keqdeeUVWNwO2svN2uFqx-kwLs" #stresstest_bot
# TOKEN = "1531582165:AAHNtmQ4lyWZ55Rkf0Hs9KxzcB0woGGeX0E" #iitmandi_bot
# TOKEN = "1546162713:AAEnv2MvukJma18_GuVqCF92NUaFYITwlBc"  #KDbot
# TOKEN = "1599589352:AAGzf5C0EjT53FsZH63_mfcdlXbJh_vmEs8" #prakharuniyalbot
TOKEN = os.getenv("TOKEN")

welcome_msg = """\n
<b>Congratulations!</b> for qualifying <u>JEE Advanced</u>\n  
This hard-earned laurel opens up for you the gateways of the IIT system where you can earn a BTech degree.
Welcome to IIT Mandi!, Beautiful Campus is worth the wait🙂\n
"""
campus_url = "https://i.ibb.co/8NbCyb9/campus.jpg"

dict_intents = set()
for doc in answers_collection.get():
    dict_intents.add(doc.get('intent'))

rec = sr.Recognizer()

SITE = StackAPI('stackoverflow')

app = Flask(__name__)


@app.route('/')
def index():
    return "Hello!"


@app.route(f'/{TOKEN}', methods=['GET', 'POST'])
def webhook():
    """webhook view which receives updates from telegram"""
    # create update object from json-format request data
    update = Update.de_json(request.get_json(), bot)
    # process update
    dp.process_update(update)
    return "ok"


def start(update, context):
    print(update)
    author = update.message.from_user.first_name
    f = open('usernames.txt', 'a')
    f.write(author + '\n')
    f.close()
    reply = "Hi! <b>{}</b>\n".format(author)
    reply += welcome_msg
    context.bot.send_photo(chat_id=update.effective_chat.id,
                           photo=campus_url,
                           caption=reply,
                           parse_mode=ParseMode.HTML)


def _help(update, context):
    help_text = "Hey! This is a help text"
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def _mess(update, context):
    context.bot.send_document(chat_id=update.effective_chat.id,
                              document=open("mess.pdf", 'rb'))


def location_handler(update, context):
    print("in location handler")
    # print(update)
    lat = update.message.location.latitude
    lng = update.message.location.longitude

    print(lat, lng)

    best_path = suggest_path(lat, lng)
    context.bot.send_message(chat_id=update.message.chat_id,
                             text=best_path,
                             parse_mode=ParseMode.HTML)


def dialogflow_connector(update, context):

    response = get_reply(update.message.text, update.message.chat_id)
    intent = response.intent.display_name

    print("--------")
    print(response)
    print("intent:->", intent)
    print("--------")

    if (intent in dict_intents):
        intent_response = answers_collection.where('intent', '==',
                                                   intent).get()[0]
        reply_text = intent_response.get('text')
        # print(reply_text)
        imgrefs = intent_response.get('imgrefs')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=reply_text,
                                 parse_mode=ParseMode.HTML)
        for imgref in imgrefs:
            context.bot.send_photo(chat_id=update.effective_chat.id,
                                   photo=imgref)

    else:
        if intent == "Default Fallback Intent":
            f = open('logs.txt', 'a')
            f.write(update.message.text + '\n')
            f.close()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=response.fulfillment_text,
                                 parse_mode=ParseMode.HTML)


def voice_to_text(update, context):

    chat_id = update.message.chat_id
    file_name = str(chat_id) + '_' + str(update.message.from_user.id) + str(
        update.message.message_id)
    update.message.voice.get_file().download(file_name + '.ogg')
    os.system('ffmpeg -i ' + file_name + '.ogg ' + file_name + '.wav')
    os.system('rm ' + file_name + '.ogg')
    harvard = sr.AudioFile(file_name + '.wav')
    with harvard as source:
        audio = rec.record(source)

    message_text = rec.recognize_google(audio)

    os.system('rm ' + file_name + '.wav')

    response = get_reply(message_text, chat_id)
    intent = response.intent.display_name

    print("--------")
    print(response)
    print("intent:->", intent)
    print("--------")

    if (intent in dict_intents):
        intent_response = answers_collection.where('intent', '==',
                                                   intent).get()[0]
        reply_text = intent_response.get('text')
        imgrefs = intent_response.get('imgrefs')
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=reply_text,
                                 parse_mode=ParseMode.HTML)
        for imgref in imgrefs:
            context.bot.send_photo(chat_id=update.effective_chat.id,
                                   photo=imgref)

    else:
        if intent == "Default Fallback Intent":
            f = open('logs.txt', 'a')
            f.write(update.message.text + '\n')
            f.close()
        context.bot.send_message(chat_id=update.effective_chat.id,
                                 text=response.fulfillment_text,
                                 parse_mode=ParseMode.HTML)


def echo_sticker(update, context):
    """callback function for sticker message handler"""
    context.bot.send_sticker(chat_id=update.effective_chat.id,
                             sticker=update.message.sticker.file_id)


def pathtoiitmandi(update, context):
    author = update.message.from_user.first_name
    help_text = "Hey {} ,Please share your live location through telegram\n".format(
        author)
    context.bot.send_message(chat_id=update.effective_chat.id, text=help_text)


def error(update, context):
    """callback function for error handler"""
    logger.error("Update '%s' caused error '%s'", update, context.error)


def stacksearch(update, context):
    query = ' '.join(context.args)

    if query == "":
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            "Send your queries like: '/programming_doubt how to make a chatbot'"
        )
        return
    results = SITE.fetch('search', intitle=query)["items"]

    if results == []:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=
            "Sorry I couldn't find anything related. You can google to find an answer on some other websites or post a question yourself."
        )
        return

    reply = u"""Here are some results:\n\n"""
    for i in range(min(5, len(results))):
        reply += """%s. <a href="%s">%s</a>\n\n""" % (
            str(i + 1), results[i]["link"], results[i]["title"])
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=reply,
                             parse_mode=ParseMode.HTML)


if __name__ == "__main__":

    url_for_webhook = "https://a2e4e59086b6.ngrok.io/"
    bot = Bot(TOKEN)
    try:
        bot.set_webhook(url_for_webhook + TOKEN)
    except Exception as e:
        print(e)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('courses', courses)],
        states={
            FIRST: [
                CallbackQueryHandler(cs, pattern='^' + str(ONE) + '$'),
                CallbackQueryHandler(ee, pattern='^' + str(TWO) + '$'),
                CallbackQueryHandler(me, pattern='^' + str(THREE) + '$'),
                CallbackQueryHandler(ce, pattern='^' + str(FOUR) + '$'),
            ],
        },
        fallbacks=[CommandHandler('courses', courses)],
    )

    dp = Dispatcher(bot, None)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", _help))
    dp.add_handler(CommandHandler("mess", _mess))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("admin", admin))

    dp.add_handler(CommandHandler("pathtoiitmandi", pathtoiitmandi))
    dp.add_handler(CommandHandler("programming_doubt", stacksearch))
    dp.add_handler(MessageHandler(Filters.text, dialogflow_connector))
    dp.add_handler(MessageHandler(Filters.sticker, echo_sticker))
    dp.add_handler(MessageHandler(Filters.location, location_handler))
    dp.add_handler(MessageHandler(Filters.voice, voice_to_text))
    dp.add_handler(MessageHandler(Filters.audio, voice_to_text))
    dp.add_error_handler(error)

    bot.set_my_commands(
        [["courses", "Know the Branch curriculum"],
         [
             "pathtoiitmandi",
             "Best way to travel to IIT MANDI from your location"
         ],
         [
             "programming_doubt",
             "Search stackoverflow for programming related doubts"
         ], ["help", "Guide to Bot"], ["mess", "Get mess menu"],
         ["admin", "Contact admin"]])

    app.run(port=8443, debug=True)
