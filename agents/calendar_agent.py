import os
import base64
import json
from dotenv import load_dotenv
from typing import List
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq
from langchain_google_community import CalendarToolkit
from langchain_google_community.calendar.utils import (
    build_resource_service, 
    get_google_credentials
)
from langchain_core.tools import tool
from langchain_core.messages import ToolMessage
from langsmith import traceable
from langchain.tools import BaseTool

path = os.path.join("..", ".env")
load_dotenv(dotenv_path=path)

os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGSMITH_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
SCOPES = json.loads(os.getenv("SCOPES"))

groq_api_key = os.getenv("GROQ_API_KEY")

model = ChatGroq(model_name="deepseek-r1-distill-llama-70b", api_key=groq_api_key)


class CalendarAgent:
    system_message = """
        You are an expert calendar assistant integrated with Google calendar via the Google calendar API. 

        You are a subagent of my personal assistant agent.

        You will be triggered when the assistant manager agent delegate a task to you, and your job as my calender manager agent is to perform actions on
            my behalf such as checking my availability, creating events, updating events, and getting my calendar events for a specific time frame.

        Depending on the task given to you by your manager, you will identify the right tools to use and in what order to achieve the task.

        After accomplishing the task you will always report back to the manager agent.

        You have access to the following tools:

        - CalendarUpdateEvent: Use this tool to update an existing calendar event. Given the event's id, use the tool decode_id to decode the event's id. You will use the output of decode_id as the id to provide to CalendarUpdateEvent.
        You will use this tool when the manager asks you to update an event in the calendar

        - CalendarSearchEvents: Use this tool to retrieve events from my calendar between two timestamps

        - CalendarCreateEvent: Use this tool to create a new event in my calendar

        - GetCurrentDatetime: Use this tool to get the current date time. You will always rely to this tool before creating, updating or searching events in my calendar.

        **# Notes**
        - You will always report back to your manager agent in as much detail as possible
        - You must always use GetCurrentDatetime to get the current date time
    """

    def __init__(self) -> None:
        path_token_file = os.path.join("shared", "token.json")
        path_credentials_file = os.path.join("shared", "credentials.json")
        credentials = get_google_credentials(
            token_file=path_token_file,
            scopes=SCOPES,
            client_secrets_file=path_credentials_file
        )
        api_resource = build_resource_service(credentials=credentials)
        self.toolkit = CalendarToolkit(api_resource=api_resource)
        self.model = model
        self.agent_executor = self.create_agent()


    @tool
    def decode_id(self, input_id: str) -> str:
        """ Tool to decode google calendar event id """
        decoded = base64.urlsafe_b64decode(input_id + '==').decode('utf-8')
        decoded = decoded.split()[0]
        return decoded
    

    def create_agent(self) -> CompiledGraph:
        """ Creates google calendar compiled graph """
        tools = self.create_tools()
        return create_react_agent(self.model, tools, prompt=CalendarAgent.system_message)


    def create_tools(self) -> List[BaseTool]:
        """ Creates the whole list of tools associated to this model """
        return [self.decode_id] + self.toolkit.get_tools()
    
    @traceable(run_type="llm", name="Calendar agent")
    def invoke(self, task: str):
        """ Performs the given task """
        response = self.agent_executor.invoke({ "messages": [{"role": "user", "content": task}] })
        return response["messages"]
    
    def handleTask(self, state):
        print(f"State: {state}")
        print("Calling calendar agent...")
        last_tool_calls = state["messages"][-1].tool_calls
        task = last_tool_calls[0]["args"]["task"]
        tool_call_id = last_tool_calls[0]["id"]
        response = self.invoke(task)
        return { "messages": [ ToolMessage(content=f"{response}", name="Delegate", tool_call_id=tool_call_id) ]}