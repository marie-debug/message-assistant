import json

from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import openai

import config
from User import User

openai.api_key = os.environ['OPENAI_API_KEY']

FINAL_MESSAGE = 'gotta go will talk later'

with open("contexts.json", "r") as f:
    contexts = json.loads(f.read())

# Create a new chatbot named Charlie
chatbot = ChatBot('Doppelganger', logic_adapters=[
    {

        'import_path': 'chatterbot.logic.BestMatch',
        'default_response': FINAL_MESSAGE,
        'maximum_similarity_threshold': 0.70
    },
])

trainer = ListTrainer(chatbot)
trainer2 = ChatterBotCorpusTrainer(chatbot)

trainer2.train(
    "chatterbot.corpus.english.greetings",
    "chatterbot.corpus.english.money",
)

trainer.train([
    "Thanks",
    "👍🏾 👍🏾",
])

trainer.train([
    "Thank you",
    "👍🏾 👍🏾",
])

trainer.train([
    "to you too",
    "👍🏾 👍🏾",
])

trainer.train([
    "okay",
    "👍🏾 👍🏾",
])

trainer.train([
    "what will you guys be up to",
    "nothing much",
])

trainer.train([
    "we miss you guys",
    "👍🏾 👍🏾",
])

trainer.train([
    "is this a new number",
    "yeah! still have old number but got ths one too. save it",
])

trainer.train([
    "new number",
    "yeah! still have old number but got ths one too. save it",
])

trainer.train([
    "new apartment",
    "gotta go will talk later",
])

trainer.train([
    "will you be coming for the holidays",
    "no leave days at all...",
])

trainer.train([
    "will you be coming for the Christmas",
    "no leave days at all...",
])

trainer.train([
    "will you be coming for the xmas",
    "no leave days at all...",
])

trainer.train([
    "hello",
    "hello",
])

trainer.train([
    "how have you been",
    "good good",
])

trainer.train([
    "can i please borrow",
    "dont have extra cash now things a tight",
])

trainer.train([
    "visa fee is",
    "dont have extra cash now things a tight",
])

trainer.train([
    "money will pay back",
    "dont have extra cash now things a tight",
])

trainer.train([
    "help with bill",
    "dont have extra cash now things a tight",
])

trainer.train([
    "help with 100 bucks",
    "dont have extra cash now things a tight",
])

trainer.train([
    "can i borrow",
    "dont have extra cash now things a tight",
])

trainer.train([
    "need help with computer",
    "have you tried to google it",
])

trainer.train([
    "need help with website",
    "have you tried to google it",
])
trainer.train([
    "are you a bot",
    "ha ha maybe maybe not ;)",
])
trainer.train([
    "are you a robot",
    "ha ha maybe maybe not ;)",
])
trainer.train([
    "are you an AI",
    "ha ha maybe maybe not ;)",
])

trainer.train([
    "say hi to everyone",
    "👍🏾 👍🏾",
])


def reply(message, active_user):
    reply = chatbot.get_response(message)
    if reply.confidence == 0:
        return get_open_ai_response(message, active_user)
    else:
        return reply.text


def get_open_ai_response(message, active_user):
    active_user_relation = active_user.Relation
    data = contexts[active_user_relation]
    persona = data["persona"]
    context = data["context"]

    prompt = "{}\n\n{}: {}\n{}: ".format(context, active_user_relation, message, persona)
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.3,
        max_tokens=60,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
        stop=[" {}:", " {}:".format(active_user_relation, persona)]
    )

    if 'choices' not in response:
        return FINAL_MESSAGE
    return response["choices"][0]["text"].strip()


"""
 The following loop will execute each time the user enters input
while True:
    try:
        active_user = SentMessage("1", "birtday", "zane", "+9111", "nephew","")
        user_input = input()
        bot_response = reply(user_input, active_user)
        print(bot_response)
    # Press ctrl-c or ctrl-d on the keyboard to exit
    except (KeyboardInterrupt, EOFError, SystemExit):
        break
"""
