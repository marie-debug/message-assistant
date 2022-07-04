import ast
import traceback

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
send_grid_key = os.environ.get('SENDGRID_API_KEY')
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')


def getDates():
    """
    returns a dictionary with dates,name and type eg:
    {
      "10/06": [
        {
          "name": "tunga",
          "type": "birthday"
        },
        {
          "name": "marion",
          "type": "birthday"
        }
      ],
      "11/06": [

    """

    with open("dates.json", "r") as f:
        dates = json.loads(f.read())
    return dates


def getTemplates():
    """
    returns a dictionary with different events types eg:
    {
      "birthday": [
        "Happy Birthday {}!",
        "Happy Birthday {} party like a rockstar!",
        "Hey, {} happy birthday have a great one"
      ],
      "halloween": [...
    """
    with open("templates.json", "r") as f:
        templates = json.loads(f.read())
    return templates


def getPeople():
    """
    returns a dictionary of people and their relation eg:
    {
      "tunga": {
        "relation": "sister"
    },
      "marion": {...

    """
    with open("people.json", "r") as f:
        people = json.loads(f.read())
    return people


with open("contexts.json", "r") as f:
    contexts = json.loads(f.read())


def healthCheck():
    """
        sends a request to healthcheck io when cron job runs and sends an error log when it fails
    """
    try:
        requests.get("https://hc-ping.com/24a68c85-cca8-4199-a3f8-719ed19cdf0f", timeout=10)
    except requests.RequestException as e:
        logger.warning("healthchecks.io ping failed: %s" % e)


@scheduler.task('cron', id='do_send_messages', hour='11', minute='0', jitter=120)
def sendMessagesCron():
    """
        runs cron job at specified time and sends messages
    """
    healthCheck()
    now = datetime.now()
    sendMessages(now.today())
    logger.info('cron ran at {} {} aest'.format(now.today(), now.strftime("%H:%M:%S")))


scheduler.start()


def getbody(type, name):
    """
        :param type: type of event e.g. birthday
        :type: str
        :param age
        :type
        :param name:the name of message receiver
        :type name: str
        :returns: random message
        :rtype: str
    """
    templates = getTemplates()
    people = getPeople()
    templateMessageList = templates[type]
    randomMessage = random.choice(templateMessageList)
    sign = ', Cheers Tunga and Marion'
    relation = people[name]["relation"]
    if relation == "nephew" or relation == "niece":
        sign = ', From Uncle Tunga and Aunt Marion'
    return randomMessage.format(name.capitalize()) + sign


def getNumberOfYears(birthdate):
    now = datetime.now().year
    birthdate = datetime.strptime(birthdate, '%d/%m/%Y').year
    years = now - birthdate
    return str(years)


def sendMessages(now):
    """
    sends messages to user then adds the user and message sent to dynamodb if it doesn't exist and sends email to admin
    :param now:is the local date and time
    :type now :datetime.datetime
    """
    users = []
    today = now.strftime("%d/%m")
    dates = getDates()

    if today not in dates:
        return
    messages = dates[today]
    for message in messages:
        to_name = message['name']
        body = getbody(message['type'], to_name)
        if to_name in phonesDict:
            from_number = os.environ['FROM']
            to_number = phonesDict[to_name]
            try:
                if message['type'] == 'birthday':
                    user = sendBirthdayMessage(body, from_number, to_number, to_name)
                else:
                    user = sendMessage(body, from_number, to_number, to_name)
                if user is not None:
                    users.append(user)
            except Exception as e:
                logger.error('Failed.', exc_info=e)
                trace = traceback.format_exc()
                sendAdminEmail(
                    'tried to send to: {} <br><br> phone number: {} <br><br> trace:<br><br> {}'.format(to_name,
                                                                                                       to_number,
                                                                                                       trace),
                    'Error sending message to {}'.format(to_name)
                )
                continue
        else:
            logger.error(message['name'] + ' is not in environment PHONES')
    sendAdminMessagedUsers(users)


def sendMessage(messageBody, messageFrom, messageToNumber, messageToName):
    """
    sends message to user

    :param messageBody:
    :type messageBody:str
    :param messageFrom:
    :type messageFrom:str
    :param messageToNumber:
    :type messageToNumber: str
    :param messageToName:
    :type messageToName: str
    :return user:
    :rtype user: User
    """
    people = getPeople()

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
    if 'birth' in people[messageToName].keys():
        age = getNumberOfYears(people[messageToName]["birth"])
    else:
        age = ''

    user = User(message.sid, messageToName, messageToNumber, relation, message.error_message,
                conversations, age)

    dynamodb.AddActiveUser(user)
    logger.info("added {} to active users table".format(messageToName))
    return user


def sendBirthdayMessage(messageBody, messageFrom, messageToNumber, messageToName):
    """
    sends message to user

    :param messageBody:
    :type messageBody:str
    :param messageFrom:
    :type messageFrom:str
    :param messageToNumber:
    :type messageToNumber: str
    :param messageToName:
    :type messageToName: str
    :return user:
    :rtype user: User
    """
    if dynamodb.GetActiveUser(messageToNumber) is not None:
        return None

    return sendMessage(messageBody, messageFrom, messageToNumber, messageToName)


def sendAdminEmail(body, subject):
    """
    sends email to admin and logs response
    :param body:
    :type body:str
    :param subject:
    :type subject:str
    """

    from_email = os.environ['FROM_EMAIL']
    admin_emails = ast.literal_eval(os.environ['ADMIN_EMAILS'])
    message = Mail(
        from_email=from_email,
        to_emails=admin_emails,
        subject=subject,
        html_content=body
    )
    try:
        sg = SendGridAPIClient(send_grid_key)
        response = sg.send(message)
        logger.info("email sent status: {} body: {}".format(response.status_code, response.body))
    except Exception as e:
        logger.error(e)


def sendAdminMessagedUsers(users):
    """
    sends email to admin and logs response
    :param users:
    :type users:list
    """
    if not users:
        return

    userStringList = []
    for user in users:
        userStringList.append(str(user))

    body = '<p>Hey! message assistant here, I have sent messages to  the following users:</p>'
    messages = '<br><br>'.join(userStringList)
    subject = 'I have just sent messages to ({})'.format(len(userStringList))
    body = body + messages
    sendAdminEmail(body, subject)


@app.route('/')
def hello_world():
    """
    return json string
    """
    return jsonify(hello='world')


@app.route('/sendtest')
def send_test():
    """
    send message to user and return json string
    """
    now = datetime.now()
    sendMessages(now.today())
    return jsonify(hello='test')


@app.route("/sms-reply", methods=['GET', 'POST'])
def incoming_sms():
    """
        gets user message checks whether active user  exists  then determines appropriate response

    """
    phone_number = request.values.get('From', None)
    active_user = dynamodb.GetActiveUser(phone_number)
    if active_user == None:
        logger.info("not replying {} because response window has closed".format(phone_number))
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
