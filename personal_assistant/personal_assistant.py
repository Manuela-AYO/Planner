from typing import TypedDict, List
from typing_extensions import Annotated
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from .delegation_tool import DelegationTool
from messages.message import Message
from agents.available_agents import available_agents
from langgraph.prebuilt import tools_condition


class State(TypedDict):
    """
    Structure of the shared state of the state graph
    """
    messages: Annotated[List, add_messages]


class PersonalAssistant:
    """ Personal assistant which will help the user perform a task """
    def __init__(self, llm):
        self.tools = [DelegationTool()]
        self.model = llm.bind_tools(self.tools)
        self.memory = MemorySaver()
        self.assistant = self.create_execution_graph()

    def create_execution_graph(self):
        """ Create the first bricks of the state graph corresponding to our assistant """
        graph_builder = StateGraph(State)

        # nodes
        graph_builder.add_node("chatbot", self.chatbot)
        for k, v in available_agents.items():
            graph_builder.add_node(k, v)

        # edges
        for key in available_agents.keys():
            graph_builder.add_edge(key, "chatbot")
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges(
            "chatbot",
            self.route_primary_assistant,
            {
                END: END,
                "calendar_agent": "calendar_agent"
            }
        )
        self.app = graph_builder.compile(checkpointer=self.memory)
        # try:
        #     image = self.app.get_graph().draw_mermaid_png()
        #     with open("image.png", "wb") as file:
        #         file.write(image)
        #     print("Finished display")
        # except Exception as e:
        #     print(f"We got an error  {e}")
        return self.app
    
    def route_primary_assistant(self, state: State):
        if isinstance(state, list):
            ai_message = state[-1]
        elif messages := state.get("messages", []):
            ai_message = messages[-1]
        else:
            raise ValueError(f"No message found in input state to tool_edge {state}")
        if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
            return "calendar_agent"
        return END
       
    def chatbot(self, state: State) -> dict:
        print("Calling chatbot...")
        response = self.model.invoke(state["messages"])
        return { "messages": [response] }

    def perform_task(self, message: Message, config: dict):
        content = message.get_new_message()
        if content:
            response = self.app.invoke({ "messages": [HumanMessage(content=content)] }, config=config)
            answer = response["messages"][-1].content
            message.send_message(answer)
            return answer
        return "No message yet"
