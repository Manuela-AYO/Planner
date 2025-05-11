from pydantic import BaseModel, Field
from typing import Type
from langchain.tools import BaseTool
from langsmith import traceable
from shared.agents_name import AGENT_NAMES


class _DelegationInput(BaseModel):
    """ Defines the structure of the arguments for the delegation tool """
    agent_name: str = Field(description=f"The name of the agent to delegate the task to. It should be one of this list {AGENT_NAMES}")
    task: str = Field(description="The task the agent should perform")


class DelegationTool(BaseTool):
    """ Tool that delegates the task to the right agent """
    name: str = "Delegate"
    description: str = "Delegate the task to the right agent"
    args_schema: Type[BaseModel] = _DelegationInput

    def delegate(self, agent_name: str, task: str) -> str:
        """ Chooses the right agent given the agent's name """
        print(f"Executing task {task} using agent {agent_name}")

        match agent_name:
            case 'Calendar agent':
                return "Use the calendar agent"
            case _:
                raise ValueError("We can't perform this task for now")

    @traceable(run_type="tool", name="Delegate")
    def _run(self, agent_name: str, task: str) -> str:
        """ Runs the delegate function """
        return self.delegate(agent_name, task)