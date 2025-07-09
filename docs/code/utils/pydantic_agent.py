
from pydantic_ai import Agent,  ToolOutput
from pydantic_ai.messages import  ModelMessage,  ModelResponse, TextPart
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.tools import Tool, ToolFuncEither, AgentDepsT

from collections.abc import  Sequence
from typing import TypeVar,Optional,Union
OutputDataT = TypeVar("OutputDataT")

class PydanticAgent():
    def __init__(
        self,
        name: str,
        model: OpenAIModel, 
        output_type: type[OutputDataT] | ToolOutput[OutputDataT],
        system_prompt: str = "You are a helpful assistant.",
        tools: Sequence[
            Tool[AgentDepsT] | ToolFuncEither[AgentDepsT, ...]
        ] = (),
    ) -> None:
        """
        Create an agent

        """
        #self.memory_lst = []
        self.name = name
        
        # 判断的是历史all_messages()的context上下文内容
        def completion_detector_hook(messages: list[ModelMessage]) -> list[ModelMessage]:  
            """检测完成标记并处理任务结束"""  
            for message in messages:  
                #print (f">>>> message:  {message} <<<<")
                if isinstance(message, ModelResponse):  
                    for part in message.parts:  
                        #print (f">>>> Part:  {part} <<<<")
                        if isinstance(part, TextPart) and part.content.strip() == "[[ ## completed ## ]]":  
                            # 找到完成标记，可以在这里添加结束逻辑  
                            # 例如：抛出自定义异常来停止执行  
                            print("任务已完成.........")
                            raise TaskCompletedException("任务已完成")

            return messages
        
        class TaskCompletedException(Exception):  
            """任务完成异常"""  
            pass

        self.agent = Agent(model=model, 
                           name=name, 
                           output_type=output_type,
                           system_prompt=system_prompt,
                           tools=tools,
                           model_settings={'tool_choice': 'auto'},
                           retries=3,
                           #history_processors=[completion_detector_hook]
                           )
    
        self.message_history: list[ModelMessage] = []
        self.last_answer=''

    def ask(self, question: str, reset_history=True, max_msg:int=10) -> str:
        
        if self.message_history == None or reset_history==True:
            result = self.agent.run_sync(
            user_prompt=question,
        )
        else:
            result = self.agent.run_sync(
            user_prompt=question,
            message_history= self.message_history[-max_msg:] if len(self.message_history) > max_msg else self.message_history
        )

        self.message_history=result.all_messages()
        self.last_answer=result.output
        
        return result.output

    def get_all_messages(self):
        """Get the memory of the agent"""
        return self.message_history
