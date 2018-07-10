#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from hermes_python.hermes import Hermes
import random
from message import Message

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

SKILL_MESSAGES = {
    'fr': {
        "noTable": "Il faut d'abord choisir une table de multiplication",
        "invalidTable": "Désolé, mais on ne joue qu'avec des tables plus grande que zéro",
        "newTable": "Ok, on fait la table des {} .",
        "newMultiplication": "Combien font {} fois {} ?",
        "wrongAnswer": [
            "Non, {} n'est pas la bonne réponse. On continue",
            "Et non, {} n'est pas la bonne réponse. Essaye une autre",
            "{} n'est pas la bonne réponse. On passe à une autre"
        ],
        "rightAnswer": [
            "Bravo. Tu marques un point. On continue",
            "Super, tu gagnes un point. On continue",
            "Bien joué, encore un point. On passe à une autre"
        ],
        "tableFinished": [
            "Bravo, tu as finis cette table! Ton score est de {} points",
            "Super, tu as terminé cette table! Ton score est de {} points",
            "Félicitation cette table est maintenant terminée! Ton score est de {} point"
        ],
        "giveUpButRemaining": [
            "Ok, la réponse c'était {} . On passe à une autre.",
            "Ne te décourage pas. la réponse c'était {} . On en fait une autre."
        ],
        "giveUpAndNoMore": [
            "Ok, la réponse était {} . Cette table est terminée! Ton score est de {} point"
        ],
        'stopGame': [
            "Ok, on arrête là. Ton score est de {} point. A bientôt.",
            "Ok, ton score est de {} point. Merci d'avoir jouer."
        ],
    }
}


class MultiplicationGame:
    def __init__(self):
        self.__current_table = 0
        self.__current_multiplier = 0
        self.__score = 0
        self.__multipliers = []
        self.__message = Message(SKILL_MESSAGES, 'fr')

    def new_multiplier(self):
        return random.choice(self.__multipliers)

    def new_multiplication(self):
        self.__current_multiplier = self.new_multiplier()
        return self.__message.get('newMultiplication').format(self.__current_table, self.__current_multiplier)

    def user_request_quiz(self, hermes, intent_message):

        if intent_message.slots.table:
            new_table = int(intent_message.slots.table.first().value)

            if new_table > 0:

                self.__score = 0
                self.__multipliers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                self.__current_table = new_table

                sentence = "{} {}".format(
                    self.__message.get('newTable').format(self.__current_table),
                    self.new_multiplication()
                )
                hermes.publish_continue_session(intent_message.session_id, sentence, INTENT_FILTER_GET_ANSWER)

            else:
                hermes.publish_end_session(intent_message.session_id, self.__message.get('invalidTable'))

    def user_gives_answer(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_continue_session(intent_message.session_id, self.__message.get('noTable'), [INTENT_START_MULTIPLICATIONTABLE_QUIZ])

        if intent_message.slots.answer:
            answer = int(intent_message.slots.answer.first().value)
            result = self.__current_multiplier * self.__current_table

            self.__multipliers.remove(self.__current_multiplier)

            if answer == result:
                self.__score = self.__score + 1

                if len(self.__multipliers) > 0:
                    hermes.publish_end_session(intent_message.session_id, self.__message.get('rightAnswer'))
                    hermes.publish_start_session_action('default', self.new_multiplication(), INTENT_FILTER_GET_ANSWER, True, '')
                else:
                    hermes.publish_end_session(intent_message.session_id, self.__message.get('tableFinished').format(self.__score))

            else:
                if len(self.__multipliers) > 0:
                    hermes.publish_end_session(intent_message.session_id, self.__message.get('wrongAnswer').format(answer))
                    hermes.publish_start_session_action('default', self.new_multiplication(), INTENT_FILTER_GET_ANSWER, True, '')
                else:
                    hermes.publish_end_session(intent_message.session_id, self.__message.get('tableFinished').format(self.__score))

    def user_does_not_know(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_end_session(intent_message.session_id, "")

        result = self.__current_multiplier * self.__current_table
        self.__multipliers.remove(self.__current_multiplier)

        if len(self.__multipliers) > 0:
            hermes.publish_end_session(intent_message.session_id, self.__message.get('giveUpButRemaining').format(result))
            hermes.publish_start_session_action('default', self.new_multiplication(), INTENT_FILTER_GET_ANSWER, True, '')

        else:
            sentence = self.__message.get('giveUpAndNoMore').format(result, self.__score)
            hermes.publish_end_session(intent_message.session_id, sentence)

    def user_quits(self, hermes, intent_message):
        if self.__current_table == 0:
            hermes.publish_end_session(intent_message.session_id, "")

        hermes.publish_end_session(intent_message.session_id, self.__message.get('stopGame').format(self.__score))

    def start(self):
        with Hermes(MQTT_ADDR) as h:
            h.subscribe_intent(INTENT_START_MULTIPLICATIONTABLE_QUIZ, self.user_request_quiz) \
                .subscribe_intent(INTENT_STOP_QUIZ, self.user_quits) \
                .subscribe_intent(INTENT_DOES_NOT_KNOW, self.user_does_not_know) \
                .subscribe_intent(INTENT_GIVE_ANSWER, self.user_gives_answer) \
                .start()


if __name__ == "__main__":
    game = MultiplicationGame()
    game.start()
