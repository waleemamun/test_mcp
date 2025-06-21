from langchain_community.llms import Ollama as LangchainOllama
import ollama
from langchain_community.llms import Ollama
import os
import sys
import requests
import base64
from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from pyboxen import boxen
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
 

class LLM:
    def __init__(self, type: str):
        # Load environment variables from .env file
        load_dotenv()
        
        if type == 'L':
            self.llm = Ollama(model="llama3.1:8b-instruct-q4_K_M")
            self.type = 'L'
        elif type == 'O':
            self.type = 'O'
            self.client_id = os.getenv('CLIENT_ID')
            self.client_secret = os.getenv('CLIENT_SECRET')
            self.cisco_openai_app_key = os.getenv('CISCO_OPENAI_APP_KEY')
            self.cisco_brain_user_id = os.getenv('CISCO_BRAIN_USER_ID')
            self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            auth_value = base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode('utf-8')).decode('utf-8')

            # Request OAuth2 token
            url = "https://id.cisco.com/oauth2/default/v1/token"
            headers = {
                "Accept": "*/*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {auth_value}"
            }
            payload = "grant_type=client_credentials"
            token_response = requests.post(url, headers=headers, data=payload)

            # Extract and return access token
            self.access_token = token_response.json().get("access_token")
            self.llm = AzureChatOpenAI(
                    deployment_name="gpt-4o-mini",
                    azure_endpoint='https://chat-ai.cisco.com',
                    api_key=self.access_token,
                    api_version="2023-08-01-preview",
                    model_kwargs=dict(
                        user=f'{{"appkey": "{self.cisco_openai_app_key}", "user": "{self.cisco_brain_user_id}"}}'
                    )
            )

    def print_question_and_answer(self, question, answer):
        print(boxen(f"{question}", title="Question", color="red"))
        print(boxen(f"{answer}", title="Answer", color="green"))
    
    def invoke(self, message:str) -> str:
        response = self.llm.invoke(message)
        self.print_question_and_answer(message, response.content)
        return response.content
    
    def count_tokens(self, text:str, tokenizer) -> int:
        if tokenizer == None:
            return len(text.split())
        tokens = tokenizer.encode(text, add_special_tokens=False)
        return len(tokens)

def get_llm():
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    cisco_openai_app_key = os.getenv('CISCO_OPENAI_APP_KEY')
    cisco_brain_user_id = os.getenv('CISCO_BRAIN_USER_ID')
    auth_value = base64.b64encode(f'{client_id}:{client_secret}'.encode('utf-8')).decode('utf-8')

    # Request OAuth2 token
    url = "https://id.cisco.com/oauth2/default/v1/token"
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {auth_value}"
    }
    payload = "grant_type=client_credentials"
    token_response = requests.post(url, headers=headers, data=payload)

    # Extract and return access token
    access_token = token_response.json().get("access_token")
    llm = AzureChatOpenAI(
            deployment_name="gpt-4o-mini",
            azure_endpoint='https://chat-ai.cisco.com',
            api_key=access_token,
            api_version="2023-08-01-preview",
            model_kwargs=dict(
                user=f'{{"appkey": "{cisco_openai_app_key}", "user": "{cisco_brain_user_id}"}}'
            )
    )
    return llm

if __name__ == '__main__':
    llm = get_llm()

    message = f"""
    What is the best book by Kazuo Ishiguro?
                """
    response = llm.invoke(message)
    print(f"Response: {response}")

