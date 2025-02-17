import json
import mimetypes
import os
from functools import wraps
from pathlib import Path
from pprint import pprint
from xml.etree import ElementTree as ET

import requests
from django.core import serializers
from django.db import IntegrityError
from django.db.models import Q
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .apiRateLimit import check_and_decrement_api_ratelimit
from .embedding import (anonymize_text, detect_entities, embed_text,
                        map_entities, return_context, vectorize, categorize, summarize_text)
from .file_importer import extract_text, save_file
from .llm import count_tokens, run_llm
from .llmManager import LLM, llmManager
from .models import (AnonymizeEntitie, Document, Room, RoomDocuments, Section,
                     User)
from .qdrant import create_collection, delete_text, insert_text, search
from .serializers import (AnonymizationMappingSerializer, DocumentSerializer,
                          ReadDocumentSerializer, RoomSerializer,
                          UserSerializer)
from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny

LLM_MAX_TOKENS = 4098

# initialize llm engine
myLLM = LLM(os.getenv("OPEN_AI_KEY"))

# Labels for Labellist
labellist = ["CARDINAL", "DATE", "EVENT", "FAC", "GPE", "LANGUAGE", "LAW", "LOC", "MONEY", "NORP", "ORDINAL", "ORG", "PERCENT", "PERSON", "PRODUCT", "QUANTITY", "TIME", "WORK_OF_ART", "PER", "MISC"]

# initialize LLM Manager
myllmManager = llmManager(myLLM)

def get_token_auth_header(request):
    """Obtains the Access Token from the Authorization Header
    """
    auth = request.META.get("HTTP_AUTHORIZATION", None)
    parts = auth.split()
    token = parts[1]

    return token

def requires_scope(required_scope):
    """Determines if the required scope is present in the Access Token
    Args:
        required_scope (str): The scope required to access the resource
    """
    def require_scope(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_auth_header(args[0])
            decoded = jwt.decode(token, verify=False)
            if decoded.get("scope"):
                token_scopes = decoded["scope"].split()
                for token_scope in token_scopes:
                    if token_scope == required_scope:
                        return f(*args, **kwargs)
            response = JsonResponse({'message': 'You don\'t have access to this resource'})
            response.status_code = 403
            return response
        return decorated
    return require_scope

def download_file(request, filename):
    # Define the path to the directory where your files are stored
    files_path = "./ExampleFiles/JuraStudium"
    # Construct the full file path
    file_path = os.path.join(files_path, filename)

    # Check if the file exists
    if os.path.exists(file_path):
        # Determine the content type based on the file extension
        content_type, _ = mimetypes.guess_type(filename)

        # Open the file with appropriate headers for download
        with open(file_path, "rb") as file:
            response = HttpResponse(file, content_type=content_type)
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            return response
    else:
        # Return a 404 Not Found response if the file doesn't exist
        return HttpResponseNotFound("File not found")


class UserApiView(APIView):
    @permission_classes([AllowAny])
    def get(self, request, auth0_id, *args, **kwargs):
        try:
            user = User.objects.get(auth0_id=auth0_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        """
        Create a user and his collection.
        """
        data = {
            "auth0_id": request.data.get("auth0_id"),
            "username": request.data.get("username"),
            "email": request.data.get("email"),
        }
        serializer = UserSerializer(data=data)

        try:
            if serializer.is_valid():
                serializer.save()
                [_, id] = request.data.get("auth0_id").split("|")
                create_collection(id)
                response = Response(serializer.data, status=status.HTTP_201_CREATED)

                # create first Room when user is created
                myllmManager.addRoom(id, "Initial Room")
            else:
                # Handle other validation errors
                response = Response(
                    serializer.errors, status=status.HTTP_400_BAD_REQUEST
                )

        except IntegrityError as e:
            # Handle the IntegrityError (duplicate key error)
            response = Response(
                {"error": "User with this auth0_id already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return response

    @permission_classes([AllowAny])
    def put(self, request, auth0_id, *args, **kwargs):
        try:
            user = User.objects.get(auth0_id=auth0_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class CategorizeApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        """
        POST method to process input text and return chapters/headings with their line numbers.
        Input:
            JSON with "text" field containing the input text.
        Response:
            JSON with a list of detected headings and their line numbers.
        """
        # Extract input text from the request
        input_text = request.data.get("text")
        
        # Validate input
        if not input_text:
            return Response(
                {"error": "No text provided. Please include a 'text' field in the request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Call the categorize method to detect headings
            headings = categorize(input_text)
            
            # Prepare the response data
            response_data = {
                "headings": [{"line": line, "heading": heading} for heading, line in headings]
            }

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle any unexpected errors
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class SummarizeApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        """
        POST method to summarize the input text.
        Input:
            JSON with "text" field containing the input text.
        Response:
            JSON with the summarized text.
        """
        # Extract input text from the request
        input_text = request.data.get("text")

        # Validate input
        if not input_text:
            return Response(
                {"error": "No text provided. Please include a 'text' field in the request."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Call the summarize_text function to generate the summary
            summary = summarize_text(input_text)
            
            # Prepare the response data
            response_data = {"summary": summary}

            return Response(response_data, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle any unexpected errors
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UploadApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        auth0_id = request.POST.get("user")
        user = User.objects.get(auth0_id=auth0_id)
        files = request.FILES.getlist("files")
        Path("../temp").mkdir(parents=True, exist_ok=True)

        documents = []
        success = True

        for file in files:
            file_size = file.size
            temp_file_path = save_file("../temp", file)
            text = extract_text(temp_file_path, file.name)
            os.remove(temp_file_path)

            document_data = {
                "filename": file.name,
                "text": text,
                "user": user.id,
                "lang": user.lang,
                "fileSize": file_size,
            }

            serializer = DocumentSerializer(data=document_data)
            if serializer.is_valid():
                result = serializer.save()
                documents.append(serializer.data)

                [_, id] = user.auth0_id.split("|")
                qdrant_result = insert_text(id, result, user.lang)
                if not qdrant_result:
                    success = False
                    break
            else:
                success = False
                break

        if not success:
            for doc in documents:
                Document.objects.filter(id=doc["id"]).delete()
            return Response("File upload failed", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(documents, status=status.HTTP_201_CREATED)


class RoomNamesApiView(APIView):
    @permission_classes([AllowAny])
    def get(self, request, *args, **kwargs):
        auth0_id = request.GET.get("user_auth0_id")

        rooms = Room.objects.filter(userID=auth0_id)
        room_data = {room.id: room.roomName for room in rooms}
        return Response(room_data, status=status.HTTP_200_OK)


class RoomsApiView(APIView):
    # get all Rooms
    @permission_classes([AllowAny])
    def get(self, request, *args, **kwargs):
        auth0_id = request.GET.get("user_auth0_id")

        rooms = Room.objects.filter(user__auth0_id=auth0_id)

        room_serializer = RoomSerializer(rooms, many=True)

        return Response(room_serializer.data, status=status.HTTP_200_OK)

    # create room
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        user_auth0_id = request.data.get("user_auth0_id")
        room_name = request.data.get("room_name")

        try:
            user = User.objects.get(auth0_id=user_auth0_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        new_room = myllmManager.addRoom(user, room_name)
        room_serializer = RoomSerializer(new_room)

        return Response(room_serializer.data, status=status.HTTP_201_CREATED)


class RoomApiView(APIView):
    # get Room
    @permission_classes([AllowAny])
    def get(self, request, room_id, *args, **kwargs):
        try:
            room = Room.objects.get(id=room_id)
            serializer = RoomSerializer(room)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )

    # delete room
    @permission_classes([AllowAny])
    def delete(self, request, room_id, *args, **kwargs):
        try:
            room = Room.objects.get(id=room_id)
            room_data = RoomSerializer(room).data
            room.delete()
            return Response(room_data, status=status.HTTP_200_OK)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # update room
    @permission_classes([AllowAny])
    def put(self, request, room_id, *args, **kwargs):
        try:
            room = Room.objects.get(id=room_id)
            data = request.data.copy()
            data.pop("user", None)
            serializer = RoomSerializer(room, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        auth0_id = request.data.get("auth0_id")
        user = User.objects.get(auth0_id=auth0_id)

        documents = Document.objects.filter(user_id=user.id)

        serializer = ReadDocumentSerializer(documents, many=True)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @permission_classes([AllowAny])
    def delete(self, request, *args, **kwargs):
        file_ids = request.data if isinstance(request.data, list) else []

        documents_to_delete = Document.objects.filter(id__in=file_ids)

        for document in documents_to_delete:
            user = document.user
            [_, id] = user.auth0_id.split("|")
            delete_text(id, document)

        deleted_count, _ = documents_to_delete.delete()

        return Response({"deletedCount": deleted_count}, status=status.HTTP_200_OK)

    @permission_classes([AllowAny])
    def put(self, request, *args, **kwargs):
        """
        Update headings and summaries for a document.
        """
        document_id = request.data.get("document_id")
        headings = request.data.get("headings")  # Expecting a list of {"line": int, "heading": str, "summary": str (optional)}

        if not document_id:
            return Response({"error": "document_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        document = Document.objects.filter(id=document_id).first()

        if not document:
            return Response({"error": "Document not found"}, status=status.HTTP_404_NOT_FOUND)

        # Ensure headings is a list of dictionaries
        if not isinstance(headings, list):
            return Response({"error": "headings must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate each heading structure
        for heading in headings:
            if not isinstance(heading, dict) or "line" not in heading or "heading" not in heading:
                return Response({"error": "Each heading must have 'line' and 'heading' fields"}, status=status.HTTP_400_BAD_REQUEST)

        # Update the document with new headings
        document.headings = headings
        document.save()

        return Response({"message": "Headings updated successfully", "document_id": document.id}, status=status.HTTP_200_OK)


class UpdateRoomDocumentsView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, room_id):
        document_ids = request.data.get("document_ids", [])

        try:
            room = Room.objects.get(id=room_id)
        except Room.DoesNotExist:
            return Response(
                {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
            )

        RoomDocuments.objects.filter(room=room).delete()

        for doc_id in document_ids:
            try:
                document = Document.objects.get(id=doc_id)
                RoomDocuments.objects.create(room=room, document=document)
            except Document.DoesNotExist:
                return Response(
                    {"error": f"Document with id {doc_id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        updated_room_serializer = RoomSerializer(room)
        return Response(updated_room_serializer.data, status=status.HTTP_200_OK)


class MessagesApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, recipient, *args, **kwargs):
        current_time = timezone.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        auth0_id = request.data.get("user", {}).get("auth0_id")
        if check_and_decrement_api_ratelimit(auth0_id) == 0:
            return Response("Trial is over.", status.HTTP_429_TOO_MANY_REQUESTS)

        # message for vDB (get facts from data)
        if recipient == "search":
            question = request.data.get("content")
            [_, id] = auth0_id.split("|")
            room_id = request.data.get("room", {}).get("id")

            user = User.objects.get(auth0_id=auth0_id)
            vector = vectorize(question)

            room = Room.objects.get(id=room_id)
            roomDocs = RoomDocuments.objects.filter(room=room)

            roomDocsList = []
            for line in roomDocs:
                roomDocsList.append(line.document.id)

            try:
                search_results = search(id, vector, roomDocsList)
            except Exception:
                return Response("Search Error", status.HTTP_400_BAD_REQUEST)

            facts = []
            counter = {}
            actual_entities = []
            for search_result in search_results:
                section = Section.objects.get(
                    id=search_result.payload.get("section_id")
                )
                embedded_text = embed_text(section.document.text, user.lang)
                (before_result, after_result) = return_context(
                    embedded_text,
                    section.doc_index,
                    room.settings.get("pre_phrase_count"),
                    room.settings.get("post_phrase_count"),
                )

                # Detect entities using Spacy
                entities = []
                for ent in embedded_text.ents:
                    entity_info = {
                        "TEXT": ent.text,
                        "START_CHAR": ent.start_char,
                        "END_CHAR": ent.end_char,
                        "LABEL": ent.label_,
                    }
                    entities.append(entity_info)

                text = section.content

                # Detect entities using Spacy
                ner_entities = detect_entities(embedded_text, user.lang)
                
                # Get actual counters from db
                for label in labellist:
                    precounter_query = AnonymizeEntitie.objects.filter(
                        entityType=label, roomID=room
                    ).order_by("-counter")[:1]

                    if len(precounter_query) == 0:
                        precounter_value = 0
                    else:
                        precounter_value = precounter_query[0].counter + 1

                    counter[label] = precounter_value

                

                entity_mapping = map_entities(ner_entities, text, counter)
                
                for entry in entity_mapping:
                    # Check if mapping already exists
                    try:
                        go = AnonymizeEntitie.objects.get(
                            deanonymized=entry, roomID=room
                        )
                    except AnonymizeEntitie.DoesNotExist:
                        # Create model if not already existing
                        AnonymizeEntitie.objects.create(
                            roomID=room,
                            anonymized=entity_mapping[entry],
                            deanonymized=entry,
                            entityType=str(entity_mapping[entry]).split("_")[0],
                            counter=str(entity_mapping[entry]).split("_")[1],
                        )

                fact = {
                    "content": text + " ",
                    "fileName": section.document.filename,
                    "accuracy": search_result.score,
                    "context_before": before_result + " ",
                    "context_after":  after_result + " ",
                }
                facts.append(fact)

            user_serialized = UserSerializer(user).data
            room_serialized = RoomSerializer(room).data

            # Create anonymized JSON answer object
            entries = AnonymizeEntitie.objects.filter(roomID=room)
            actual_entities = AnonymizationMappingSerializer(entries, many=True).data

            response = {
                "user": user_serialized,
                "room": room_serialized,
                "role": "system",
                "content": facts,
                "created_at": current_time,
                "entities": actual_entities,
            }

            return Response(response, status.HTTP_200_OK)


        # message for llm
        elif recipient == "chatgpt":
            question = request.data.get("content")
            room_data = request.data.get("room")
            user_data = request.data.get("user")

            room_id = room_data.get("id")
            is_demo = request.query_params.get("demo", "false").lower() == "true"
            selected_model = request.data.get("model", "gpt-3.5-turbo")

            try:
                myRoom = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                return Response(
                    {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
                )

            auth0_id = user_data.get("auth0_id")

            try:
                user = User.objects.get(auth0_id=auth0_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                answer = myllmManager.llm.run(myRoom, question, model=selected_model, is_demo=is_demo)
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            user_serialized = UserSerializer(user).data
            room_serialized = RoomSerializer(myRoom).data

            response = {
                "user": user_serialized,
                "room": room_serialized,
                "role": "assistant",
                "content": answer,
                "created_at": current_time,
                "model": selected_model,  # Include model in response for transparency
            }
            return Response(response, status.HTTP_200_OK)
        
        # message for web search
        elif recipient == "websearch":
            question = request.data.get("content")
            room_data = request.data.get("room")
            user_data = request.data.get("user")
            room_id = room_data.get("id")
            is_demo = request.query_params.get("demo", "false").lower() == "true"
            selected_model = request.data.get("model", "gpt-3.5-turbo")  # 获取用户选择的模型

            try:
               myRoom = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                return Response(
                    {"error": "Room not found"}, status=status.HTTP_404_NOT_FOUND
                )

            auth0_id = user_data.get("auth0_id")

            try:
               user = User.objects.get(auth0_id=auth0_id)
            except User.DoesNotExist:
                return Response(
                    {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                # 调用 llm.run 时设置 is_web_search=True
                answer = myllmManager.llm.run(
                    myRoom, 
                    question, 
                    model=selected_model,  
                    is_web_search=True,    # Explicitly specify this is a web search
                    is_demo=is_demo
                )
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

            user_serialized = UserSerializer(user).data
            room_serialized = RoomSerializer(myRoom).data

            response = {
                "user": user_serialized,
                "room": room_serialized,
                "role": "assistant",
                "content": answer,
                "created_at": current_time,
                "model": selected_model,
            }
            return Response(response, status.HTTP_200_OK)


class NextCloudApiView(APIView):
    @permission_classes([AllowAny])
    def get(self, request, *args, **kwargs):
        """
        Creates a connection to an nextcloud instance.
        """
        session = request.session
        nextcloud_user = request.GET.get("nextCloudUserName")
        nextcloud_client_id = request.GET.get("clientId")
        nextcloud_client_secret = request.GET.get("clientSecret")
        nextcloud_authorization_url = request.GET.get("authorizationUrl")
        redirect_uri = request.GET.get("redirectUri")

        FILES_URL = (
            f"{nextcloud_authorization_url}/remote.php/dav/files/{nextcloud_user}/"
        )
        TOKEN_URL = f"{nextcloud_authorization_url}/index.php/apps/oauth2/api/v1/token"
        AUTHORIZATION_URL = (
            f"{nextcloud_authorization_url}/index.php/apps/oauth2/authorize"
        )

        data = {
            "client_id": nextcloud_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "read",
        }

        session["clientSecret"] = nextcloud_client_secret
        session["authorizationUrl"] = nextcloud_authorization_url
        session["clientId"] = nextcloud_client_id
        session["nextcloudUser"] = nextcloud_user
        session["token_url"] = TOKEN_URL
        session["files_url"] = FILES_URL
        session["redirect_uri"] = redirect_uri

        url = (
            AUTHORIZATION_URL
            + "?"
            + "&".join([f"{key}={value}" for key, value in data.items()])
        )
        return redirect(url)


class NextCloudFilesApiView(APIView):
    @permission_classes([AllowAny])
    def get(self, request, *args, **kwargs):
        session = request.session
        code = request.GET.get("code")
        nextcloud_authorization_url = session.get("authorizationUrl")
        nextcloud_client_secret = session.get("clientSecret")
        nextcloud_client_id = session.get("clientId")
        nextcloud_user = session.get("nextcloudUser")
        TOKEN_URL = session.get("token_url")
        FILES_URL = session.get("files_url")
        REDIRECT_URI = session.get("redirect_uri")

        Path("temp").mkdir(parents=True, exist_ok=True)

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": nextcloud_client_id,
            "client_secret": nextcloud_client_secret,
        }
        response = requests.post(TOKEN_URL, data=payload)
        access_token = response.json().get("access_token")
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.request("PROPFIND", FILES_URL, headers=headers)

            if response.status_code != 207:
                return "Fehler beim Abrufen der Dateien", 500

            root = ET.fromstring(response.content)
            files = [
                elem.text
                for elem in root.findall(".//{DAV:}href")
                if elem.text[-1] != "/"
            ]

        text_content = ""
        for file in files:
            filename = file.split("/")[-1]  # Dateiname aus der URL extrahieren
            file_ext = os.path.splitext(filename)[1].lower()

            download_url = f"{nextcloud_authorization_url}{file}"
            temp_file_path = os.path.join("../", "temp", filename)

            # Datei manuell herunterladen
            response = requests.get(
                download_url, headers={"Authorization": f"Bearer {access_token}"}
            )
            with open(temp_file_path, "wb") as f:
                f.write(response.content)

        return Response(
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Nextcloud File Explorer</title>
            </head>
            <body>
                <h1>Nextcloud File Explorer</h1>
                {text_content}
            </body>
            </html>
        """
        )


class LanguageAPI(APIView):
    @permission_classes([AllowAny])
    def get(self, request, *args, **kwargs):
        try:
            auth0_id = request.GET["auth0_id"]
            user = User.objects.get(auth0_id=auth0_id)
            return Response(user.lang, status.HTTP_200_OK)
        except:
            return Response("Error!", status.HTTP_500_INTERNAL_SERVER_ERROR)

    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        try:
            lang = request.data.get("language")
            auth0 = request.data.get("auth0_id")
            user = User.objects.get(auth0_id=auth0)
            user.lang = lang["key"]
            user.save()

            return Response(user.lang, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response("User not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FilesApiView(APIView):
    @permission_classes([AllowAny])
    def post(self, request, *args, **kwargs):
        auth0_id = request.data["auth0_id"]
        user = User.objects.get(auth0_id=auth0_id)
        [_, id] = auth0_id.split("|")
        create_collection(id)

        documents = Document.objects.filter(user=user)
        success = True
        for document in documents:
            Section.objects.filter(document=document).delete()

            qdrant_result = insert_text(id, document, document.lang)
            if qdrant_result != True:
                success = False

        if success:
            return Response([], status=status.HTTP_200_OK)
        else:
            return Response("File upload failed", status=status.HTTP_400_BAD_REQUEST)
