# Import the openai package
import os
from pprint import pprint
from duckduckgo_search import DDGS

import openai

from .models import ContextEntry, Room, RoomSettings, User

# Set openai.api_key to the OPENAI environment variable
openai.api_key = os.getenv("OPEN_AI_KEY")


class ContextEntry:
    """represents one context line in the form:
    "role": Message role, "content": Message content
    """

    def __init__(self, role, content):
        self.role = role
        self.content = content


class Room_:
    """room class holds the context and anonymization data
    atm just saves the data in memory.
    TODO
        implement persistent memory (db)
    """

    def __init__(self, userID):
        self.userID: str = userID  # owner
        self.anonymizeCompleteContext: bool = False
        self.anonymizeMap: List[Dict] = []
        self.context: List[ContextEntry] = []

    def appendContext(self, role, content):
        self.context.append(ContextEntry(role, content))

    def createFullMessage(self, question):
        tempMessage: List[Dict] = []

        for line in self.context:
            messageLine = {"role": line.role, "content": line.content}
            tempMessage.append(messageLine)

        tempMessage.append({"role": "user", "content": question})

        return tempMessage


class LLM:
    def __init__(self, apiKey):
        self.apiKey = apiKey
        openai.api_key = self.apiKey

    def perform_web_search(self, query, num_results=3):
        try:
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=num_results))
            formatted_results = "\n".join([
                f"- {result['title']}: {result['body']}"
                for result in search_results
            ])
            return formatted_results
        except Exception as e:
            print(f"Error: {str(e)}")
            return "Error"

    def run(self, room: Room, question: str, model: str, is_web_search: bool = False, is_demo: bool = False):
        """
        Run a chat request to the selected OpenAI model.

        :param room: Room object containing chat context.
        :param question: The user's question.
        :param model: The OpenAI model to use ("gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini").
        :param is_demo: Flag to indicate if it's a demo mode.
        :return: The assistant's response.
        """
        # 验证模型
        valid_models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"]
        if model not in valid_models:
            raise ValueError(f"Invalid model '{model}'. Choose from {valid_models}")

        room.appendContext(room, "user", question, is_demo)

        if is_web_search:
           
            search_results = self.perform_web_search(question)
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that can provide up-to-date information based on web search results. Please analyze the search results and provide a comprehensive answer."
                },
                {
                    "role": "user",
                    "content": f"Based on the following search results, answer the question:\n\nQuestion: {question}\n\nSearch Results:\n{search_results}"
                }
            ]
        else:
            messages = room.createFullMessage(room, False, is_demo, question)


        #  API call parameters
        api_params = {
            "model": model,  # 直接使用用户选择的模型
            "messages": messages,
            "temperature": 0.7,
        }

        print("Sending API parameters:", api_params)

        # 调用OpenAI API
        response = openai.ChatCompletion.create(**api_params)
        response_content = response["choices"][0]["message"]["content"]

        if not response_content:
            response_content = "I apologize, I cannot generate an appropriate response. Please try rephrasing your question."

        # Add the response to context
        room.appendContext(room, "assistant", response_content, is_demo)
        return response_content



class llmManager:
    def __init__(self, llm):
        self.llm: LLM = llm

    def addRoom(self, user_, name_):
        room_settings = RoomSettings(prompt_template_lang="en")
        new_room = Room(user=user_, name=name_, settings=room_settings.to_dict())
        new_room.save()

        return new_room

    def getRoom(self, auth0_id, room_id):
        try:
            user = User.objects.get(auth0_id=auth0_id)
            myRoom = Room.objects.get(user=user, id=room_id)
            return myRoom
        except (User.DoesNotExist, Room.DoesNotExist):
            return None
