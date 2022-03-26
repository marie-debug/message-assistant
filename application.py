import ast
from flask import Flask, jsonify
import os
from twilio.rest import Client
import json
from datetime import date
import random
from flask_apscheduler import APScheduler
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


# set configuration values
class Config:
    SCHEDULER_API_ENABLED = True


# create app
application = Flask(__name__)
app = application
app.config.from_object(Config())

# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
scheduler.init_app(app)

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)
phonesDict = ast.literal_eval(os.environ["PHONES"])
from_number = os.environ['FROM']
send_grid_key = os.environ.get('SENDGRID_API_KEY')
admin_emails = ast.literal_eval(os.environ['ADMIN_EMAILS'])
from_email = os.environ['FROM_EMAIL']

with open("dates.json", "r") as f:
    dates = json.loads(f.read())

with open("templates.json", "r") as f:
    templates = json.loads(f.read())


@scheduler.task('cron', id='do_send_messages', hour='22', minute='0', jitter=120)
def sendMessagesCron():
    now = date.today()
    sendmessages(now)
    print('cron ran at {}'.format(now))


scheduler.start()


def getbody(type, name):
    templateMessageList = templates[type]
    randomMessage = random.choice(templateMessageList)
    return randomMessage.format(name.capitalize()) + '\nCheers Tunga and Marion'


def sendmessages(now):
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
            else:
                print(message['name'] + ' is not in environment PHONES')
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
        print("email sent status: {} body: {}".format(response.status_code, response.body))
    except Exception as e:
        print(e)


@app.route('/')
def hello_world():  # put application's code her
    # Find your Account SID and Auth Token at twilio.com/console
    # and set the environment variables. See http://twil.io/secure
    return jsonify(hello='world')


if __name__ == '__main__':
    app.run()
