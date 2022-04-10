import ast

import requests
from flask import Flask, jsonify, request
import os
from twilio.rest import Client
import json
from datetime import date, datetime, timedelta
import random
from flask_apscheduler import APScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import logging
from logging.handlers import RotatingFileHandler
from twilio.twiml.messaging_response import MessagingResponse
import bot
import dynamodb
from User import User

try:
    import zoneinfo
except ImportError:
    from backports import zoneinfo

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logger.setLevel(logging.DEBUG)


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = zoneinfo.ZoneInfo('Australia/Brisbane')


# create app
application = Flask(__name__)
app = application
app.config.from_object(Config())

handler = RotatingFileHandler('/opt/python/log/application.log', maxBytes=1024, backupCount=5)
handler.setFormatter(formatter)
application.logger.addHandler(handler)

# initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)
phonesDict = ast.literal_eval(os.environ["PHONES"])
from_number = os.environ['FROM']
send_grid_key = os.environ.get('SENDGRID_API_KEY')
admin_emails = ast.literal_eval(os.environ['ADMIN_EMAILS'])
from_email = os.environ['FROM_EMAIL']
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')

with open("dates.json", "r") as f:
    dates = json.loads(f.read())

with open("templates.json", "r") as f:
    templates = json.loads(f.read())

with open("people.json", "r") as f:
    people = json.loads(f.read())

with open("contexts.json", "r") as f:
    contexts = json.loads(f.read())


@scheduler.task('cron', id='do_send_messages', hour='8', minute='0', jitter=120)
def sendMessagesCron():
    try:
        requests.get("https://hc-ping.com/24a68c85-cca8-4199-a3f8-719ed19cdf0f", timeout=10)
    except requests.RequestException as e:
        logger.warning("healthchecks.io ping failed: %s" % e)

    now = datetime.now()
    sendMessages(now.today())
    logger.info('cron ran at {} {} aest'.format(now.today(), now.strftime("%H:%M:%S")))


scheduler.start()


def getbody(type, name):
    templateMessageList = templates[type]
    randomMessage = random.choice(templateMessageList)
    sign = ', Cheers Tunga and Marion'
    relation = people[name]["relation"]
    if relation == "nephew" or relation == "niece":
        sign = ', From Uncle Tunga and Aunt Marion'
    return randomMessage.format(name.capitalize()) + sign


def sendMessages(now):
    sent_messages_strings = []
    today = now.strftime("%d/%m")
    if today in dates:
        messages = dates[today]
        for message in messages:
            to_name = message['name']
            body = getbody(message['type'], to_name)
            if to_name in phonesDict:
                to_number = phonesDict[to_name]
                sent_message = sendmessage(body, from_number, to_number, to_name, message['type'])
                sent_messages_strings.append(str(sent_message))
                if dynamodb.GetActiveUser(to_name) == None:
                    dynamodb.AddActiveUser(sent_message)
                    logger.info("added {} to active users table".format(to_name))
            else:
                logger.error(message['name'] + ' is not in environment PHONES')
        sendAdminEmail(sent_messages_strings)


def sendmessage(messageBody, messageFrom, messageToNumber, messageToName, messageType):
    message = client.messages.create(
        body=messageBody,
        from_=messageFrom,
        to=messageToNumber
    )

    relation = people[messageToName]["relation"]
    data = contexts[relation]
    persona = data["persona"]
    context = data["context"]

    conversations = [
        "{}\n\n".format(context),
        "{}: {}".format(persona, messageBody),
    ]

    return User(message.sid, messageType, messageToName, messageToNumber, relation, message.error_message,
                conversations)


def sendAdminEmail(sent_messages_strings):
    body = '<p>Hey! message assistant here, I have sent the following messages</p>'
    messages = '<br><br>'.join(sent_messages_strings)
    message = Mail(
        from_email=from_email,
        to_emails=admin_emails,
        subject='I have just sent messages to ({})'.format(len(sent_messages_strings)),
        html_content=body + messages
    )
    try:
        sg = SendGridAPIClient(send_grid_key)
        response = sg.send(message)
        logger.info("email sent status: {} body: {}".format(response.status_code, response.body))
    except Exception as e:
        logger.error(e)


@app.route('/')
def hello_world():
    return jsonify(hello='world')


@app.route('/sendtest')
def send_test():
    # now = datetime.now()
    # sendMessages(now.today())
    return jsonify(hello='test')


@app.route("/sms-reply", methods=['GET', 'POST'])
def incoming_sms():
    phone_number = request.values.get('From', None)
    active_user = dynamodb.GetActiveUser(phone_number)
    if active_user == None:
        logger.info("not replaying {} because response window has closed".format(phone_number))
        return ""
    # Get the message the user
    body = request.values.get('Body', None)
    logger.info("received:" + body)
    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    reply = bot.reply(body, active_user)
    logger.info("replay:" + reply)
    resp.message(reply)
    if reply == bot.FINAL_MESSAGE:
        dynamodb.RemoveActiveUser(phone_number)
    return str(resp)


if __name__ == '__main__':
    app.run()
