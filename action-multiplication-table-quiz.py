#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
import random

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "localhost"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_START_MULTIPLICATIONTABLE_QUIZ = "alrouen:startMultiplicationTableQuiz"
INTENT_GIVE_ANSWER = "alrouen:giveAnswerToMultiplication"
INTENT_STOP_QUIZ = "alrouen:stopQuiz"
INTENT_DOES_NOT_KNOW = "alrouen:iDoNotKnow"

INTENT_FILTER_GET_ANSWER = [
    INTENT_GIVE_ANSWER,
    INTENT_STOP_QUIZ,
    INTENT_DOES_NOT_KNOW
]

class MultiplicationGame:
    def __init__(self):
        self.__current_table = 0
        self.__current_multiplier = 0
        self.__score = 0
        self.__multipliers = []

    def new_multiplier(self):
        return random.choice(self.__multipliers)

    def new_multiplication(self):
        self.__current_multiplier = self.new_multiplier()
        return "Combien font {} fois {} ?".format(self.__current_table, self.__current_multiplier)

    def user_request_quiz(self, hermes, intent_message):
        sentence = ""

        if intent_message.slots.table:
            new_table = int(intent_message.slots.table.first().value)

            if new_table > 0:
                if self.__current_table == 0 or new_table != self.__current_table:
                    self.__current_table = new_table
                    sentence = "Ok, on fait la table des {} .".format(self.__current_table)

                sentence = "{} {}".format(sentence, self.new_multiplication())
                hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)

            else:
                hermes.publish_end_session(intent_message.session_id, "Désolé, mais on ne joue qu'avec des tables positives et non nulle")

    def user_gives_answer(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_end_session(intent_message.session_id, "")

        if intent_message.slots.answer:
            answer = int(intent_message.slots.answer.first().value)
            result = self.__current_multiplier * self.__current_table

            self.__multipliers.remove(self.__current_multiplier)

            if answer == result:
                self.__score = self.__score + 1

                if len(self.__multipliers) > 0:
                    sentence = "Bravo. Tu marques un point. On continue. {}".format(self.new_multiplication())
                    hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)
                else:
                    sentence = "Bravo, tu as finis cette table! Ton score est de {} point".format(self.__score)
                    hermes.publish_end_session(intent_message.session_id, sentence)

            else:
                if len(self.__multipliers) > 0:
                    sentence = "Ce n'est pas la bonne réponse. On continue. {}".format(self.new_multiplication())
                    hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)
                else:
                    sentence = "Cette table est terminée! Ton score est de {} point".format(self.__score)
                    hermes.publish_end_session(intent_message.session_id, sentence)


    def user_does_not_know(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_end_session(intent_message.session_id, "")

        result = self.__current_multiplier * self.__current_table
        self.__multipliers.remove(self.__current_multiplier)

        if len(self.__multipliers) > 0:
            sentence = "Ok, la réponse c'était {} . On passe à une autre. {}".format(result, self.new_multiplication())
            hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)

        else:
            sentence = "Ok, la réponse était {} . Cette table est terminée! Ton score est de {} point".format(result, self.__score)
            hermes.publish_end_session(intent_message.session_id, sentence)

    def user_quits(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_end_session(intent_message.session_id, "")

        hermes.publish_end_session(intent_message.session_id, "Ok, on arrête là. Ton score est de {} point. A bientôt".format(self.__score))

    def session_started(self, hermes, session_started_message):
        self.__score = 0
        self.__multipliers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    def session_stopped(self, hermes, session_ended_message):
        hermes
        self.__current_table = 0
        self.__current_multiplier = 0
        self.__score = 0

    def start(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intent(INTENT_START_MULTIPLICATIONTABLE_QUIZ, self.user_request_quiz) \
                .subscribe_intent(INTENT_STOP_QUIZ, self.user_quits) \
                .subscribe_intent(INTENT_DOES_NOT_KNOW, self.user_does_not_know) \
                .subscribe_intent(INTENT_GIVE_ANSWER, self.user_gives_answer) \
                .subscribe_session_started(self.session_started) \
                .subscribe_session_ended(self.session_stopped) \
                .start()


if __name__ == "__main__":
    game = MultiplicationGame()
    game.start()


"""
NLU structure sample :

hermes/nlu/query
{
	"input":"donne moi la table des cinq",
	"intentFilter":null,
	"id":"8321623a-c614-4c13-95fc-ce3e1d1d8d3a",
	"sessionId":"d6becee7-dced-4a42-b7b4-02835543cbb5"
}
hermes/nlu/intentParsed 
{
	"id":"8321623a-c614-4c13-95fc-ce3e1d1d8d3a",
	"input":"donne moi la table des cinq",
	"intent":{
		"intentName":"alrouen:startMultiplicationTableQuiz",
		"probability":1.0
	},
	"slots":[ 
		{
			"rawValue":"cinq",
			"value":{
				"kind":"Number",
				"value":5.0
			},
			"range": { 
				"start":23,
				"end":27
			},
			"entity":"snips/number",
			"slotName":"table"
		}
	],
	"sessionId":"d6becee7-dced-4a42-b7b4-02835543cbb5"
}


"""