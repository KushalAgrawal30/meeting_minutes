from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools.gmail_tool import GmailTool

llm = LLM(
    model="gemini/gemini-2.0-flash",
)

@CrewBase
class Gmailcrew():
    """Gmailcrew crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def gmail_draft_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['gmail_draft_agent'],
            verbose=True,
            tools=[GmailTool()],
            llm=llm
        )
    
    @task
    def gmail_draft_task(self) -> Task:
        return Task(
            config=self.tasks_config['gmail_draft_task'], 
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Gmailcrew crew"""

        return Crew(
            agents=self.agents, 
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
