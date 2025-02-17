import os
from pprint import pprint

import tiktoken
from django.db import models
from django.db.models import JSONField
from langchain.llms import OpenAI
from django.utils import timezone


from .room_settings import RoomSettings

LLM_MAX_TOKENS = 4098

token_encoder = "cl100k_base"  # used for ChatGPT 3.5 Turbo and ChatGPT 4
llm = OpenAI(openai_api_key=os.getenv("OPEN_AI_KEY"))
encoder = tiktoken.get_encoding(token_encoder)


class User(models.Model):
    auth0_id = models.CharField(max_length=255, unique=True, null=False)
    username = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    lang = models.CharField(max_length=2, default="en")  # using ISO 639-1 codes
    max_api_calls = models.IntegerField(default=50)  
    last_reset_date = models.DateField(auto_now_add=True)  # Field to track when API call limit was last reset

    def reset_api_calls_if_needed(self):
        today = timezone.now().date()
        if self.last_reset_date < today or (self.last_reset_date == today and self.max_api_calls == 0):
            self.max_api_calls = 50
            self.last_reset_date = today
            self.save()

    def __str__(self):
        return self.auth0_id


class Document(models.Model):
    filename = models.CharField(max_length=255)
    text = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=False)
    lang = models.CharField(max_length=2, default="en")
    fileSize = models.PositiveIntegerField(default=0)
    uploadedAt = models.DateTimeField(auto_now_add=True)
    headings = models.JSONField(blank=True, null=True)

    def __str__(self):
        return self.filename


class Section(models.Model):
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, blank=True, null=False
    )
    content = models.TextField()
    doc_index = models.IntegerField()

    def __str__(self):
        return self.document.filename


class Room(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=False)
    name = models.CharField(max_length=255, default="Room")
    anonymizeCompleteContext = models.BooleanField("Anonymize Switch", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    settings = JSONField(default=RoomSettings().to_dict)

    def __str__(self):
        return f"{self.user.auth0_id} + {self.id}"

    def appendContext(self, room, role, content, is_demo):
        myContext = ContextEntry(roomID=room, role=role, content=content)
        if not is_demo:
            myContext.save()

    def createFullMessage(self, room, get_all, is_demo, question):
        fullMessage: List[Dict] = []
        msg_length = 0
        if is_demo:
            question_line = {"role": "user", "content": question}
            system_line = {
                "role": "system",
                "content": self.settings["prompt_template"],
            }
            fullMessage.append(question_line)
            fullMessage.append(system_line)
        else:
            context = ContextEntry.objects.filter(roomID=room).order_by("-created_at")    
            
            for line in context:
                content = line.content
                messageLine = {"role": line.role, "content": content}
                token_size = len(encoder.encode(str(messageLine)))
                msg_length = msg_length + token_size

                if not get_all:
                    if msg_length < LLM_MAX_TOKENS:
                        fullMessage.append(messageLine)
                    else:
                        break  # stop
                else:
                    fullMessage.append(messageLine)
            systemLine = {"role": "system", "content": room.settings["prompt_template"]}
            fullMessage.append(systemLine)

        fullMessage.reverse()
        return fullMessage


class ContextEntry(models.Model):
    roomID = models.ForeignKey(Room, on_delete=models.CASCADE)
    role = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class AnonymizeEntitie(models.Model):
    roomID = models.ForeignKey(Room, on_delete=models.CASCADE)
    anonymized = models.CharField(max_length=255, null=False)
    deanonymized = models.CharField(max_length=255, null=False)
    entityType = models.CharField(max_length=255, null=False)
    counter = models.IntegerField()

    class Meta:
        unique_together = (
            "deanonymized",
            "roomID",
        )


class RoomDocuments(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
