

from typing import Optional, Union, Generator, Dict, List
from base64 import b64encode
import fake_useragent
import tls_client
import requests
import uuid
import json
import logging

from pydantic import BaseModel
from typing import List, Optional, Union

from typing import List, Dict
from pydantic import BaseModel
import json
import uuid

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from base64 import b64encode, b64decode
import hashlib

def Encrypt(data: b64encode, key: str) -> bytes:
    hash_key: hashlib.sha256 = hashlib.sha256(key.encode()).digest()
    iv: bytes = get_random_bytes(16)
    cipher: AES = AES.new(hash_key, AES.MODE_CBC, iv)
    encrypted_data: cipher.encrypt = cipher.encrypt(PadData(data.encode()))
    return iv.hex() + encrypted_data.hex()

def PadData(data):
    block_size: int = AES.block_size
    padding_size: int = block_size - len(data) % block_size
    padding: bytes = bytes([padding_size] * padding_size)
    return data + padding

class Conversation():
	@classmethod
	def __init__(self: type, model: type) -> None:
		self.__model: type = model

	@classmethod
	def GetList(self: type) -> List[Dict[str, str]]:
		self.__model._UpdateJWTToken()
		PAYLOAD: Dict[str, str] = {
		   "0":{
		      "json":{
		         "workspaceId": self.__model._WORKSPACEID
		      }
		   },
		   "1":{
		      "json":{
		         "workspaceId": self.__model._WORKSPACEID
		      }
		   }
		}

		return self.__model._session.get(f"{self.__model._API}/chat.loadTree,personas.listPersonas?batch=1&input={json.dumps(PAYLOAD)}", headers=self.__model._HEADERS).json()[0]["result"]["data"]["json"][0]["data"]
		

	@classmethod
	def Rename(self: type, id: str, name: str) -> None:
		conversations: List[Dict[str, str]] = self.GetList()
		PAYLOAD: Dict[str, str] = {
			"0": {
				"json": {
					"id": id,
					"name": name,
					"workspaceId": self.__model._WORKSPACEID
				}
			}
		}

		for cv in conversations:
			if id == cv["id"]:
				DATA_: object = self.__model._session.post(f"{self.__model._API}/chat.renameChat?batch=1", json=PAYLOAD, headers=self.__model._HEADERS)

				if DATA_.status_code == 200:
					self.__model._logger.debug(f"Renamed conversation ({id}) to ({name}).")
				else:
					self.__model._logger.error(f"Error on rename the conversation {id}")
					return None

	@classmethod
	def GenerateName(self: type, message: str) -> str:
		__PAYLOAD: Dict[str, str] = {
			"0": {
				"json": {
					"messages": [
						{
							"id": "",
							"content": message,
							"parentId": str(uuid.uuid4()),
							"role": "user",
							"createdAt": "",
							"model": self.__model._model
						}
					]
				},
				"meta": {
					"values": {
						"messages.0.createdAt": ["Date"]
					}
				}
			}
		}
		Suggestion: Dict[str, str] = self.__model._session.post(f"{self.__model._API}/chat.generateName?batch=1", 
											  headers=self.__model._HEADERS, json=__PAYLOAD).json()
		return Suggestion[0]["result"]["data"]["json"]["title"]


	@classmethod
	def Remove(self: type, id: str) -> None:
		conversations: List[Dict[str, str]] = self.GetList()
		PAYLOAD: Dict[str, str] = {
			"0": {
				"json": {
					"id": id,
					"workspaceId": self.__model._WORKSPACEID
				}
			}
		}

		for cv in conversations:
			if id == cv["id"]:
				DATA_: object = self.__model._session.post(f"{self.__model._API}/chat.removeChat?batch=1", 
									 json=PAYLOAD, headers=self.__model._HEADERS)

				if DATA_.status_code == 200:
					self.__model._logger.debug(f"Deleted conversation ({id}).")
				else:
					self.__model._logger.error(f"Error on delete conversation {id}")
					return None

	@classmethod
	def GetMessages(self: type, id: str) -> List[Dict[str, str]]:
		__PAYLOAD: Dict[str, str] = {
			"0": {
				"json": {
					"chatId": id,
					"workspaceId": self.__model._WORKSPACEID
				}
			}
		}
		DATA_: Dict[str, str] = self.__model._session.post(f"{self.__model._API}/chat.getMessagesByChatId?batch=1", 
										headers=self.__model._HEADERS, json=__PAYLOAD)

		if DATA_.status_code != 200:
			self.__model._logger.error(f"Error on get messages of conversation ({id})")
			return {}

		return DATA_.json()[0]["result"]["data"]["json"]["messages"]

	@classmethod
	def ClearAll(self: type) -> None:
		conversations: List[Dict[str, str]] = self.GetList()
		ct: int = 0

		for cv in conversations:
			if cv["type"] == "chat":
				self.Remove(cv["id"])
				ct += 1

		print(f"Deleted ({ct}) conversation(s).")

class EmailResponse(BaseModel):
	sessionID: str
	client: str

class DeltaResponse(BaseModel):
	content: Optional[Union[str, None]] = ''

class ChoicesResponse(BaseModel):
	index: int
	finish_reason: Optional[Union[str, None]] = ''
	delta: DeltaResponse
	usage: Optional[Union[str, None]] = ''

class ForeFrontResponse(BaseModel):
	model: str
	choices: List[ChoicesResponse]

class Model:
	@classmethod
	def __init__(self: object, sessionID: str, client: str, model: Optional[str] = "gpt-3.5-turbo", 
		conversationID: Optional[Union[str, None]] = None
	) -> None:
		self._SETUP_LOGGER()
		self.Conversation: Conversation = Conversation(model=self)
		self._session: requests.Session = requests.Session()
		self._model: str = model
		self._API = "https://chat-api.tenant-forefront-default.knative.chi.coreweave.com/api/trpc"
		self.__NAME: Union[str, None] = None
		self._WORKSPACEID: str = ''
		self._USERID: str = "user_"
		self._CLIENT: str = client
		self._SESSION_ID: str = sessionID
		self.CONVERSATION_ID: List[Union[str, None]] = conversationID
		self._PERSONA: str = "607e41fe-95be-497e-8e97-010a59b2e2c0"
		self._JSON: Dict[str, str] = {}
		self._HEADERS: Dict[str, str] = {
			"Authority": "streaming.tenant-forefront-default.knative.chi.coreweave.com",
			"Accept": "*/*",
			"Accept-Language": "en,pt-BR,fr-FR;q=0.9,fr;q=0.8,es-ES;q=0.7,es;q=0.6,en-US;q=0.5,am;q=0.4,de;q=0.3",
			"Authorization": f"Bearer {self._CLIENT}",
			"Cache-Control": "no-cache",
			"Pragma": "no-cache",
			"Content-Type": "application/json",
			"Origin": "https://chat.forefront.ai",
			"Referer": "https://chat.forefront.ai/",
			"Sec-Ch-Ua": "\"Chromium\";v=\"112\", \"Not:A-Brand\";v=\"99\"",
			"Sec-Ch-Ua-mobile": "?0",
			"Sec-Ch-Ua-platform": "\"macOS\"",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "cross-site",
			"User-Agent": fake_useragent.UserAgent().random
		}

		self._JWT_HEADERS: Dict[str, str] = {
			"Authority": "clerk.forefront.ai",
			"Accept": "*/*",
			"Cache-Control": "no-cache",
			"Content-Type": "application/x-www-form-urlencoded",
			"Origin": "https://chat.forefront.ai",
			"Pragma": "no-cache",
			"Cookie": f"__client={self._CLIENT}",
			"Sec-Ch-Ua": "\"Chromium\";v=\"112\", \"Google Chrome\";v=\"112\", \"Not:A-Brand\";v=\"99\"",
			"Sec-Ch-Ua-mobile": "?0",
			"Sec-Ch-Ua-platform": "\"macOS\"",
			"Referer": "https://chat.forefront.ai/",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
			"User-Agent": fake_useragent.UserAgent().random
		}

		self._WORKSPACEID = self._GetWorkspaceID()
		self._USERID = self._GetUserID()
		self._logger.debug("Connected in Workspace: " + self._WORKSPACEID)

	@classmethod
	def _SETUP_LOGGER(self: type) -> None:
		self._logger: logging.getLogger = logging.getLogger(__name__)
		self._logger.setLevel(logging.DEBUG)
		console_handler: logging.StreamHandler = logging.StreamHandler()
		console_handler.setLevel(logging.DEBUG)
		formatter: logging.Formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		console_handler.setFormatter(formatter)

		self._logger.addHandler(console_handler)

	@classmethod
	def _UpdateJWTToken(self: type) -> None:
		jwt_token: Dict[str, str] = {}
		jwt_status: int = 0

		while True:
			jwt_token = self._session.post(f"https://clerk.forefront.ai/v1/client/sessions/{self._SESSION_ID}/tokens?_clerk_js_version=4.39.0", 
			headers=self._JWT_HEADERS)
			jwt_status = jwt_token.status_code

			if jwt_status == 200:
				break

		self._HEADERS["Authorization"] = f"Bearer {jwt_token.json()['jwt']}"

	@classmethod
	def _UpdateXSignature(self: type) -> None:
		DATA_: str = b64encode((self._USERID + self._PERSONA + self._WORKSPACEID).encode()).decode()
		self._HEADERS["X-Signature"] = Encrypt(DATA_, self._SESSION_ID)

	@classmethod
	def _GetUserID(self: type) -> str:
		DATA_: Dict[str, str] = self._session.post(f"https://clerk.forefront.ai/v1/client/sessions/{self._SESSION_ID}/touch?_clerk_js_version=4.39.0",
																headers=self._JWT_HEADERS).json()
		return DATA_["response"]["user"]["id"]

	@classmethod
	def _GetWorkspaceID(self: type) -> str:
		self._UpdateJWTToken()
		url: str = f"{self._API}/workspaces.listWorkspaces,chat.loadTree?batch=1&input="
		payload: str = "{\"0\":{\"json\":null,\"meta\":{\"values\":[\"undefined\"]}},\"1\":{\"json\":{\"workspaceId\":\"\"}}}"
		return self._session.get(url + payload, headers=self._HEADERS).json()[0]["result"]["data"]["json"][0]["id"]

	@classmethod
	def SetupConversation(self: type, prompt: str, options: Optional[Dict[str, str]] = {}) -> None:
		action = "new"
		conversations: Dict[str, str] = self.Conversation.GetList()
		if self.CONVERSATION_ID is None:
			if conversations[-1]["type"] == "chat":
				self.CONVERSATION_ID = conversations[-1]["id"]
				action = "continue"
		else:
			action = "continue"

		if "create" in options:
			if options["create"]:
				action = "new"

				if "name" not in options:
					self.__logger.error("Invalid options.")
					return None

				for cv in conversations:
					if cv["name"].lower() != options["name"].lower():
						self.__NAME = options["name"]

		self._JSON = {
			"text": prompt,
			"action": action,
			"id": self.CONVERSATION_ID,
			"parentId": self._WORKSPACEID,
			"workspaceId": self._WORKSPACEID,
			"messagePersona": self._PERSONA,
			"model": self._model
		}

	@classmethod
	def IsAccountActive(self: type) -> bool:
		return self._session.post(f"https://clerk.forefront.ai/v1/client/sessions/{self._SESSION_ID}/touch?_clerk_js_version=4.39.0", 
			headers=self._JWT_HEADERS).status_code == 200

	@classmethod
	def SendConversation(self: type) -> Generator[ForeFrontResponse, None, None]:
		self._UpdateJWTToken()
		self._UpdateXSignature()

		for chunk in self._session.post("https://streaming.tenant-forefront-default.knative.chi.coreweave.com/chat", 
			headers=self._HEADERS, json=self._JSON, stream=True
		).iter_lines():
			if b"finish_reason\":null" in chunk:
				data = json.loads(chunk.decode('utf-8').split("data: ")[1])
				# print(data)
				yield ForeFrontResponse(**data)
			# print('---------')
			# print(chunk)
			# print('---------')


		# conversations: List[Dict[str, str]] = self.Conversation.GetList()
		# if self.__NAME is not None:
		# 	self.Conversation.Rename(conversations[-1]["id"], self.__NAME)
		# 	self.__NAME = None
		# else:
		# 	if conversations[-1]["name"].lower() == "new chat":
		# 		conversation: Dict[str, str] = conversations[-1]
		# 		self.Conversation.Rename(conversation["id"], self.Conversation.GenerateName(self._JSON["text"]))
				



from typing import Dict

import re
import json
import logging
import fake_useragent
import tls_client



from typing import Dict, List, Union
import tls_client
import fake_useragent

class TempMail:
	@classmethod 
	def __init__(self: type) -> None:
		self.__api: str = "https://web2.temp-mail.org"
		self.__session: tls_client.Session = tls_client.Session(client_identifier="chrome_110")

		self.__HEADERS: Dict[str, str] = {
			"Authority": "web2.temp-mail.org",
			"Accept": "*/*",
			"Accept-Language": "pt-BR,en;q=0.9,en-US;q=0.8,en;q=0.7",
			"Authorization": f"Bearer {self.__GetTokenJWT()}",
			"Origin": "https://temp-mail.org",
			"Referer": "https://temp-mail.org/",
			"Sec-Ch-Ua": "\"Chromium\";v=\"112\", \"Google Chrome\";v=\"112\", \"Not:A-Brand\";v=\"99\"",
			"Sec-Ch-Ua-mobile": "?0",
			"Sec-Ch-Ua-platform": "\"macOS\"",
			"Sec-Fetch-Dest": "empty",
			"Sec-Fetch-Mode": "cors",
			"Sec-Fetch-Site": "same-site",
			"User-Agent": fake_useragent.UserAgent().random
		}

	@classmethod
	def __GetTokenJWT(self: type) -> str:
		DATA_: Dict[str, str] = self.__session.post(f"{self.__api}/mailbox").json()

		self.__EMAIL: str = DATA_["mailbox"]
		return DATA_["token"]

	@property
	def GetAddress(self: type) -> str:
		return f"{self.__EMAIL}"

	@classmethod
	def GetMessages(self: type) -> List[Dict[str, str]]:
		messages: Union[List, List[Dict[str, str]]] = []

		messages = self.__session.get(f"{self.__api}/messages", headers=self.__HEADERS).json()["messages"]

		return messages

	@classmethod
	def GetMessage(self: type, id: str) -> Dict[str, str]:
		DATA_: object = self.__session.get(f"{self.__api}/messages/{id}", headers=self.__HEADERS)

		if DATA_.status_code != 200:
			return "Invalid ID."

		return DATA_.json()

class Email:
	@classmethod
	def __init__(self: type) -> None:
		self.__SETUP_LOGGER()
		self.__session: tls_client.Session = tls_client.Session(client_identifier="chrome_110")

	@classmethod
	def __SETUP_LOGGER(self: type) -> None:
		self.__logger: logging.getLogger = logging.getLogger(__name__)
		self.__logger.setLevel(logging.DEBUG)
		console_handler: logging.StreamHandler = logging.StreamHandler()
		console_handler.setLevel(logging.DEBUG)
		formatter: logging.Formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
		console_handler.setFormatter(formatter)

		self.__logger.addHandler(console_handler)

	@classmethod
	def __AccountState(self: object, output: str, field: str) -> bool:
		if field not in output:
			return False
		return True

	@classmethod
	def CreateAccount(self: object):
		Mail = TempMail()
		MailAddress = Mail.GetAddress

		self.__session.headers = {
			"Origin": "https://accounts.forefront.ai",
			"User-Agent": fake_useragent.UserAgent().random
		}

		self.__logger.debug("Checking URL")
		
		output = self.__session.post("https://clerk.forefront.ai/v1/client/sign_ups?_clerk_js_version=4.39.0", data={"email_address": MailAddress})

		if not self.__AccountState(str(output.text), "id"):
			self.__logger.error("Failed to create account :(")
			return "Failed"

		trace_id = output.json()["response"]["id"]

		output = self.__session.post(f"https://clerk.forefront.ai/v1/client/sign_ups/{trace_id}/prepare_verification?_clerk_js_version=4.39.0", 
			data={"strategy": "email_link", "redirect_url": "https://accounts.forefront.ai/sign-up/verify"})

		if not self.__AccountState(output.text, "sign_up_attempt"):
			self.__logger.error("Failed to create account :(")
			return "Failed"

		self.__logger.debug("Verifying account")

		while True:
			messages: Mail.GetMessages = Mail.GetMessages()

			if len(messages) > 0:
				message: Dict[str, str] = Mail.GetMessage(messages[0]["_id"])
				verification_url = re.findall(r"https:\/\/clerk\.forefront\.ai\/v1\/verify\?token=\w.+", message["bodyHtml"])[0]
				if verification_url:
					break

		r = self.__session.get(verification_url.split("\"")[0])
		__client: str = r.cookies["__client"]

		output = self.__session.get("https://clerk.forefront.ai/v1/client?_clerk_js_version=4.39.0")
		token: str = output.json()["response"]["sessions"][0]["last_active_token"]["jwt"]
		sessionID: str = output.json()["response"]["last_active_session_id"]

		self.__logger.debug("Created account!")

		return EmailResponse(**{"sessionID": sessionID, "client": __client})