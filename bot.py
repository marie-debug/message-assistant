from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer

FINAL_MESSAGE = 'gotta go will talk later'
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
    "new apartment",
    "gotta go will talk later",
])

trainer.train([
    "will you be coming for the holidays",
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


def reply(message):
    reply = chatbot.get_response(message)
    return reply.text


# The following loop will execute each time the user enters input
"""
while True:
    try:
        user_input = input()

        bot_response = chatbot.get_response(user_input)

        print(bot_response)

    # Press ctrl-c or ctrl-d on the keyboard to exit
    except (KeyboardInterrupt, EOFError, SystemExit):
        break
"""
