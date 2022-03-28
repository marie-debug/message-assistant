import ast

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


@scheduler.task('cron', id='do_send_messages', hour='20', minute='0', jitter=120)
def sendMessagesCron():
    now = date.today()
    sendMessages(now)
    logger.info('cron ran at {} gmt'.format(now))


scheduler.start()


def getbody(type, name):
    templateMessageList = templates[type]
    randomMessage = random.choice(templateMessageList)
    return randomMessage.format(name.capitalize()) + '\nCheers Tunga and Marion'


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
                if dynamodb.IsUserActive(to_number) == False:
                    logger.info("added {}to active users table".format(to_number))
                    dynamodb.AddActiveUser(to_number)
            else:
                logger.error(message['name'] + ' is not in environment PHONES')
        sendAdminEmail(sent_messages_strings)


def sendmessage(messageBody, messageFrom, messageToNumber, messageToName, messageType):
    message = client.messages.create(
        body=messageBody,
        from_=messageFrom,
        to=messageToNumber
    )

    return {"type": messageType, "sentTo": messageToName, "id": message.sid, "error": message.error_message}


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


@app.route("/sms-reply", methods=['GET', 'POST'])
def incoming_sms():
    _from = request.values.get('From', None)
    if dynamodb.IsUserActive(_from) == False:
        logger.info("not replaying {} because response window has closed".format(_from))
        return ""
    # Get the message the user
    body = request.values.get('Body', None)
    logger.info("received:" + body)
    # Start our TwiML response
    resp = MessagingResponse()

    # Determine the right reply for this message
    reply = bot.reply(body)
    logger.info("replay:" + reply)
    resp.message(reply)
    if reply == bot.FINAL_MESSAGE:
        dynamodb.RemoveActiveUser(_from)
    return str(resp)


if __name__ == '__main__':
    app.run()
