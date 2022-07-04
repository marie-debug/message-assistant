import json
from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer
from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import openai
import config
import dynamodb
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
        'maximum_similarity_threshold': 0.80
    },
])

trainer = ListTrainer(chatbot)
trainer2 = ChatterBotCorpusTrainer(chatbot)

trainer2.train(
    "chatterbot.corpus.english.greetings",
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
    "what will you be up to",
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
    "vist us soon",
    "👍🏾 👍🏾",
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
    "dont have extra cash now things are tight",
])

trainer.train([
    "money will pay back",
    "dont have extra cash now things are tight",
])

trainer.train([
    "help with bill",
    "dont have extra cash now things are tight",
])

trainer.train([
    "help with 100 bucks",
    "dont have extra cash now things are tight",
])

trainer.train([
    "can i borrow",
    "dont have extra cash now things are tight",
])

trainer.train([
    "can i borrow money",
    "dont have extra cash now things are tight",
])

trainer.train([
    "do you have extra money",
    "dont have extra cash now things a tight",
])

trainer.train([
    "do you have extra cash",
    "dont have extra cash now things are tight",
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
    """
    returns a response to the input from chatterbot if confidence is zero else response is returned from openai
    then updates user conversation  in dynamodb
    :param message:
    :type message: str
    :param active_user:
    :type active_user:User
    :return response:
    """
    bot_reply = chatbot.get_response(message)
    active_user_relation = active_user.Relation
    data = contexts[active_user_relation]
    persona = data["persona"]

    if bot_reply.confidence == 0:
        active_user.Conversation.append("{}: {}".format(active_user_relation, message))
        active_user.Conversation.append("{}: ".format(persona))
        prompt = "\n".join(active_user.Conversation)

        response = get_open_ai_response(active_user_relation, persona, prompt)
        active_user.Conversation[-2] = ("{}: {}".format(active_user_relation, message))
        active_user.Conversation[-1] = ("{}: {}".format(persona, response))
    else:
        response = bot_reply.text
        active_user.Conversation.append("{}: {}".format(active_user_relation, message))
        active_user.Conversation.append("{}: {}".format(persona, response))

    dynamodb.UpdateActiveUserConversation(active_user)

    return response


def get_open_ai_response(active_user_relation, persona, prompt):
    """
         generates text reply based on user conversation context
    :param active_user_relation:
    :type: str
    :param persona:
    :type: str
    :param prompt:
    :type: str
    :return openai reply:
    :rtype: str
    """
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.3,
        max_tokens=240,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
        stop=[" {}:", " {}:".format(active_user_relation, persona)]
    )

    if 'choices' not in response:
        return FINAL_MESSAGE

    ai_reply = response["choices"][0]["text"].strip()

    if unsafe(ai_reply):
        return FINAL_MESSAGE

    return ai_reply


def unsafe(content_to_classify):
    """
    Checks and detects whether text may be sensitive or unsafe
    :param content_to_classify:
    :type content_to_classify: str
    :return: str
    """
    response = openai.Completion.create(
        engine="content-filter-alpha",
        prompt="<|endoftext|>" + content_to_classify + "\n--\nLabel:",
        temperature=0,
        max_tokens=1,
        top_p=0,
        logprobs=10
    )
    output_label = response["choices"][0]["text"]

    # This is the probability at which we evaluate that a "2" is likely real
    # vs. should be discarded as a false positive
    toxic_threshold = -0.355

    if output_label == "2":
        # If the model returns "2", return its confidence in 2 or other output-labels
        logprobs = response["choices"][0]["logprobs"]["top_logprobs"][0]

        # If the model is not sufficiently confident in "2",
        # choose the most probable of "0" or "1"
        # Guaranteed to have a confidence for 2 since this was the selected token.
        if logprobs["2"] < toxic_threshold:
            logprob_0 = logprobs.get("0", None)
            logprob_1 = logprobs.get("1", None)

            # If both "0" and "1" have probabilities, set the output label
            # to whichever is most probable
            if logprob_0 is not None and logprob_1 is not None:
                if logprob_0 >= logprob_1:
                    output_label = "0"
                else:
                    output_label = "1"
            # If only one of them is found, set output label to that one
            elif logprob_0 is not None:
                output_label = "0"
            elif logprob_1 is not None:
                output_label = "1"

            # If neither "0" or "1" are available, stick with "2"
            # by leaving output_label unchanged.

    # if the most probable token is none of "0", "1", or "2"
    # this should be set as unsafe
    if output_label not in ["0", "1", "2"]:
        output_label = "2"

    return output_label == "2"


"""
import ast
# The following loop will execute each time the user enters input
while True:
    try:
        phonesDict = ast.literal_eval(os.environ["PHONES"])
        active_user = dynamodb.GetActiveUser(phonesDict["tunga"])
        user_input = input()
        bot_response = reply(user_input, active_user)
        print(bot_response)
    # Press ctrl-c or ctrl-d on the keyboard to exit
    except (KeyboardInterrupt, EOFError, SystemExit):
        break
"""
