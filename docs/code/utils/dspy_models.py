from typing import Optional

import dspy
 
from .debug_logfire import logfire
from .models import Classify, ModeratorEvaluationOutDSPy
 
class Classifier:
    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: Optional[str] = None,
        name: str='Classifier',
    ) -> None:
        """
        Initialize a classification agent that uses DSPy to classify questions.

        Args:
            model (Agent): The model name or configuration.
            api_key (str): API key for the language model service.
            api_base (Optional[str]): Base URL for the API (e.g., Azure or custom OpenAI endpoint).
        """
        # 初始化语言模型
        self.lm = dspy.LM(
            model=model,
            api_key=api_key,
            api_base=api_base
        )
        self.name = name
        # 设置全局默认语言模型
        # dspy.settings.configure(lm=self.lm )

    def classify_question(self, context: str) -> str:
        """
        Classifies the given question using a DSPy Predict module.

        Args:
            question (str): Input question to be classified.

        Returns:
            str: Classification result.
        """
        try:
            
            with dspy.context(lm = self.lm): 
                predict_module = dspy.Predict(Classify)
                #predict_module = dspy.ChainOfThought(Classify)
                result = predict_module(context=context)
                logfire.info(f'{self.name} run',  context=self.lm.history[-1] if self.lm.history else None)

                return result  # 假设返回结果字段是 answer
        except Exception as e:
            print(f"Error during classification: {e}")
            return "unknown"

# 定制评估函数
class Evaluator:
    def __init__(
        self,
        model: str,
        api_key: str ,
        api_base: str,
        signature: str,
        instructions: Optional[str] = None,
        name: str='Evaluator'
    ) -> None:
        """
        Initialize a classification agent that uses DSPy to classify questions.

        Args:
            model (Agent): The model name or configuration.
            api_key (str): API key for the language model service.
            api_base (Optional[str]): Base URL for the API (e.g., Azure or custom OpenAI endpoint).
        """
        # 初始化语言模型
        self.lm = dspy.LM(
            model=model,
            api_key=api_key,
            api_base=api_base
        )
        self.signature = signature
        self.instructions = instructions
        self.name = name
        # 设置全局默认语言模型
        # dspy.settings.configure(lm=self.lm )

    def run(self, **kwargs) -> str:
        """
        Classifies the given question using a DSPy Predict module.

        Args:
            question (str): Input question to be classified.

        Returns:
            str: Classification result.
        """
        try:
            with dspy.context(lm = self.lm): 
                signature = dspy.Signature(signature=self.signature, instructions=self.instructions)
                classify = dspy.Predict(signature)
                result = classify(**kwargs)
                logfire.info(f'{self.name} run',  context=self.lm.history[-1] if self.lm.history else None)
                return result # 假设返回结果字段是 answer

        except Exception as e:
            print(f"Error during classification: {e}")
            return "unknown"

class Moderator:
    def __init__(
        self,
        model: str,
        api_key: str,
        api_base: Optional[str] = None,
        name: str='Moderator',
    ) -> None:
        """
        Initialize a classification agent that uses DSPy to classify questions.

        Args:
            model (Agent): The model name or configuration.
            api_key (str): API key for the language model service.
            api_base (Optional[str]): Base URL for the API (e.g., Azure or custom OpenAI endpoint).
        """
        # 初始化语言模型
        self.lm = dspy.LM(
            model=model,
            api_key=api_key,
            api_base=api_base
        )
        self.name = name
        # 设置全局默认语言模型
        # dspy.settings.configure(lm=self.lm )

    def run(self, debate_context: str) -> str:
        """
        Classifies the given question using a DSPy Predict module.

        Args:
            question (str): Input question to be classified.

        Returns:
            str: Classification result.
        """
        try:

            with dspy.context(lm = self.lm): 
                predict_module = dspy.Predict(ModeratorEvaluationOutDSPy)
                #predict_module = dspy.ChainOfThought(ModeratorEvaluationOutDSPy)
                result = predict_module(debate_context=debate_context)

                logfire.info(f'{self.name} run',  context=self.lm.history[-1] if self.lm.history else None)
                #print(self.lm.history[-1] if self.lm.history else None)
                return result  # 假设返回结果字段是 answer
        except Exception as e:
            print(f"Error during evaluation: {e}")
            return "unknown"
