"""
MAD: Multi-Agent Debate with Large Language Models
Copyright (C) 2023  The MAD Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import pydantic_ai
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.tools import Tool, ToolFuncEither, AgentDepsT

from collections.abc import  Sequence

from typing import Union,Literal

from .debug_logfire import logfire
from .pydantic_agent import PydanticAgent
from .dspy_models import Evaluator, Moderator

# 定义辩论双方的角色名称
DEBATER_ROLES = [
    "Affirmative",  # 替代原 "Affirmative"，意为支持方
    "Negative"    # 替代原 "Negative"，意为反对方
]

# 定义主持人角色名称
MODERATOR_ROLE = "Moderator"  # 替代原 "Moderator"，意为评估者或主持人
JUDGE_ROLE = "Judge"  # 

class DebatePlayer(PydanticAgent):
    def __init__(
        self,
        name: str,
        model: OpenAIModel,
        output_type: str,
        system_prompt: str = "You are a helpful assistant.",
        tools: Sequence[
                    Tool[AgentDepsT] | ToolFuncEither[AgentDepsT, ...]
                ] = (),
    ) -> None:
        super().__init__(name, model, output_type, system_prompt, tools)

class Debate:
    def __init__(self,
            model_name: str='Qwen/Qwen2.5-7B-Instruct',
            temperature: float=0, 
            num_players: int=3, 
            openai_api_key: str=None,
            base_url: str='https://api.siliconflow.cn/v1',
            tools: Sequence[
                    Tool[AgentDepsT] | ToolFuncEither[AgentDepsT, ...]
                ] = (),
            config: dict=None,
            max_round: int=3,
            sleep_time: float=0
        ) -> None:

        self.model_name = model_name
        self.temperature = temperature
        self.num_players = num_players
        self.openai_api_key = openai_api_key
        self.base_url = base_url
        self.tools=tools


        self.config = config
        self.config_init = config.copy()

        self.max_round = max_round
        self.sleep_time = sleep_time

        self.aff_ans = ""
        self.neg_ans = ""
        self.mod_ans = {}
        self.result = {}

        # 初始化pandantic_ai模型
        self.agent_model = OpenAIModel(
            #'Qwen/Qwen3-8B'
            model_name=self.model_name, #THUDM/GLM-4-9B-0414', #
            provider=OpenAIProvider(
                base_url=self.base_url,
                api_key=self.openai_api_key
            ),
        )

        # 创建并初始化代理
        self.creat_agents()
        #self.init_agents()

    def init_prompt(self, topic: str):
        """替换配置中的主题占位符"""

        #  初始化配置中的主题占位符
        self.config= self.config_init.copy()

        for key in ["player_meta_prompt", "moderator_meta_prompt", "affirmative_prompt"]:
            if key in self.config:
                self.config[key] = self.config[key].replace("##debate_topic##", topic)

    
    def creat_agents(self):
        """创建辩论参与者：正方、反方、主持人及评估者"""
        # 辩论玩家
        self.players = [
            DebatePlayer(
                name=name,
                model=self.agent_model,
                output_type=str,
                system_prompt=self.config['player_meta_prompt'],
                tools=self.tools
            )
            for name in DEBATER_ROLES
        ]
        self.affirmative, self.negative = self.players

        # 主持人 | DSPy
        self.moderator = Moderator(
            model=f'openai/{self.model_name}',
            api_key=self.openai_api_key,
            api_base=self.base_url,
            name=MODERATOR_ROLE,
        )

        # 评委 | DSPy
        signature = "debate_text -> supported_side: Literal['Affirmative', 'Negative']"
        instructions = (
            "Please carefully analyze the current situation. "
            "Consider both supporting and opposing arguments, and evaluate which side is more convincing."
        )
        self.judge_eval = Evaluator(
            name='judge_eval',
            model=f'openai/{self.model_name}',
            api_key=self.openai_api_key,
            api_base=self.base_url,
            signature=signature,
            instructions=instructions
        )


        # 答案评估器 | DSPy
        signature = "context -> answer: str"
        instructions = (
            "You are a helpful assistant tasked with answering the user's question directly, accurately, and in alignment with the provided context. Follow these steps:\n\n"
            "1. Carefully read and fully understand the user's question: `[[ ## user question ## ]]`.\n"
            "2. Analyze the provided context thoroughly to ensure your answer reflects its tone, perspective, and factual basis: `[[ ## context ## ]]`.\n"
            "3. Construct an answer that is clear, concise, logically structured, and directly addresses the question.\n"
            "4. Maintain the style and format of the original context as closely as possible, avoiding markdown or any special formatting.\n"
            "5. If the question involves reasoning, analysis, or inference, clearly explain your thought process while staying grounded in the context.\n"
            "6. Ensure your response is factually consistent with the information given and does not introduce unsupported claims or assumptions."
        )
        self.answer_eval = Evaluator(
            name='final_answer',
            model=f'openai/{self.model_name}',
            api_key=self.openai_api_key,
            api_base=self.base_url,
            signature=signature,
            instructions=instructions
        )

    def round_dct(self, num: int) -> str:
        """返回序数英文表示"""
        return {
            1: 'first', 2: 'second', 3: 'third', 4: 'fourth', 5: 'fifth',
            6: 'sixth', 7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth'
        }.get(num, str(num))

    def print_answer(self):
        """打印最终结果"""
        print("\n\n===== Debate Done! =====")
        print("\n----- Debate Topic -----")
        print(self.config.get("debate_topic", "No topic provided."))
        print("\n----- Base Answer -----")
        print(self.result.get("base_answer", "No base answer provided."))
        print("\n----- Debate Answer -----")
        print(self.result.get("debate_answer", "No debate answer provided."))
        print("\n----- Debate Reason -----")
        print(self.result.get("reason", "No reason provided."))

    def get_answer(self) -> str:
        """获取最终答案"""
        return self.result['debate_answer']

    '''
    def broadcast(self, msg: str):
        """Broadcast a message to all players. 
        Typical use is for the host to announce public information

        Args:
            msg (str): the message
        """
        # print(msg)
        #logfire.info('>> BroadCast Msg: {BroadCast}', BroadCast=msg)
        for player in self.players:
            player.add_event(msg)
            logfire.info('>> BroadCast: to [{BroadCast}], msg: {msg}', BroadCast=player.name, msg=msg)

    def speak(self, speaker: str, msg: str):
        """The speaker broadcast a message to all other players. 

        Args:
            speaker (str): name of the speaker
            msg (str): the message
        """
        if not msg.startswith(f"{speaker}: "):
            msg = f"{speaker}: {msg}"

        # print(msg)
        for player in self.players:
            if player.name != speaker:
                player.add_event(msg)
                logfire.info('>> Speak: to [{Speak}], msg: {Msg}', Speak=speaker, Msg=msg)

    def ask_and_speak(self, player: DebatePlayer):
        ans = player.ask()
        #player.add_memory(ans)
        self.speak(player.name, ans)
    '''

    def run_loop(self, debate_topic: str=None):
        """运行多轮辩论流程，直到对方回复[END]，或达到最大回合数"""

        # 设置辩论主题
        if debate_topic:
        
            # 初始化提示语
            self.init_prompt(debate_topic)
            self.config['debate_topic'] = debate_topic
        else:
            print(f"Please set debate topic: {debate_topic}")
            return

        # 执行第一轮辩论
        for round_num in range(self.max_round):
            if round_num == 0:
                logfire.info('===== Debate Round-1 =====')
                # 正方首次发言
                self.aff_ans = self.affirmative.ask(self.config['affirmative_prompt'])
                self.result['base_answer'] = self.aff_ans

                # 反方首次回应
                neg_prompt = self.config['negative_prompt'].replace('##aff_ans##', self.aff_ans).replace("##debate_topic##", self.config['debate_topic'])
                self.neg_ans = self.negative.ask(neg_prompt)

            else:
                logfire.info('===== Debate Round-{Round} =====', Round=round_num + 1)
                
                # 正方根据反方上轮回答进行反驳
                aff_prompt = self.config['debate_prompt_loop'].replace('##oppo_ans##', self.neg_ans)
                self.aff_ans = self.affirmative.ask(aff_prompt, reset_history=False)

                # 反方根据正方本轮回答进行反驳
                neg_prompt = self.config['debate_prompt_loop'].replace('##oppo_ans##', self.aff_ans)
                self.neg_ans = self.negative.ask(neg_prompt, reset_history=False)
            
            # 检查是否有一方已经完成辩论，包含特定的结束标记：`[[ ## completed ## ]]`
            #  正方没有新的意见，结束辩论，反方胜利
            if self._is_debate_completed(self.aff_ans) :
                print(f'Debate completed by : Affirmative')
                self._set_supported_side('Negative')
                break

            #  反方没有新的意见，结束辩论，正方胜利
            elif self._is_debate_completed(self.neg_ans):
                print(f'Debate completed by : Negative') 
                self._set_supported_side('Affirmative')
                break
            else:
                self._set_supported_side('')

        # 到达最大回合或主持人已经给出结论
        if self._has_supported_side():
            answer_result = self._generate_final_answer(self._has_supported_side())
            self.result.update({
                    'debate_answer': answer_result.answer,
                    'reason': f"{self._has_supported_side()} side was more convincing.",
                    'success': True
                })

        else:
            # 启动裁判机制，由 Judge 决定胜负
            judge_result = self._get_judge_decision()

            # 最终答案生成
            answer_result = self._generate_final_answer(judge_result.supported_side)
            if answer_result.answer:
                self.result.update({
                    'debate_answer': answer_result.answer,
                    'reason': f"{judge_result.supported_side} side was more convincing.",
                    'success': True
                })

    def run(self, debate_topic: str=None):
        """运行辩论流程，每一轮由主持人进行评估，直到有一方胜出或达到最大回合数"""
        # 设置辩论主题
        if debate_topic:
            self.config['debate_topic'] = debate_topic
        else:
            print(f"Please set debate topic: {debate_topic}")
            return

        # 初始化提示语
        self.init_prompt(debate_topic)

        # 执行第一轮辩论
        for round_num in range(self.max_round):
            if round_num == 0:
                logfire.info('===== Debate Round-1 =====')
                # 正方首次发言
                self.aff_ans = self.affirmative.ask(self.config['affirmative_prompt'])
                self.result['base_answer'] = self.aff_ans

                # 反方首次回应
                neg_prompt = self.config['negative_prompt'].replace('##aff_ans##', self.aff_ans)
                self.neg_ans = self.negative.ask(neg_prompt)

                round_info = 'first'
            else:
                logfire.info('===== Debate Round-{Round} =====', Round=round_num + 1)
                
                # 正方根据反方上轮回答进行反驳
                aff_prompt = self.config['debate_prompt'].replace('##oppo_ans##', self.neg_ans)
                self.aff_ans = self.affirmative.ask(aff_prompt)

                # 反方根据正方本轮回答进行反驳
                neg_prompt = self.config['debate_prompt'].replace('##oppo_ans##', self.aff_ans)
                self.neg_ans = self.negative.ask(neg_prompt)

                round_info = self.round_dct(round_num + 1)

            # 主持人评价
            mod_prompt = (self.config['moderator_prompt']
                        .replace('##aff_ans##', self.aff_ans)
                        .replace('##neg_ans##', self.neg_ans)
                        .replace('##round##', round_info))

            try:
                response = self.moderator.run(debate_context=mod_prompt)
                self.mod_ans.update({
                    'supported_side': response.supported_side,
                    'reason': response.reason,
                })
                #print("Raw model output:", self.mod_ans)
            except pydantic_ai.exceptions.UnexpectedModelBehavior as e:
                print("Error occurred during moderation:", str(e))
                raise

            # 检查是否已有最终答案
            if self._has_supported_side():
                break

        # 到达最大回合或主持人已经给出结论
        if self._has_supported_side():
            answer_result = self._generate_final_answer(self._has_supported_side())
            self.result.update({
                    'debate_answer': answer_result.answer,
                    'reason': f"{self._has_supported_side()} side was more convincing.",
                    'success': True
                })

        else:
            # 启动裁判机制，由 Judge 决定胜负
            judge_result = self._get_judge_decision()

            # 最终答案生成
            answer_result = self._generate_final_answer(judge_result.supported_side)
            if answer_result.answer:
                self.result.update({
                    'debate_answer': answer_result.answer,
                    'reason': f"{judge_result.supported_side} side was more convincing.",
                    'success': True
                })

    # ————————————————————————————————
    # 辅助函数
    # ————————————————————————————————
    def _has_supported_side(self) -> bool:
        """检查主持人是否已经给出支持方"""
        supervised_side = self.mod_ans.get("supported_side", None)
        if supervised_side in ['Affirmative', 'Negative']: # 'Neutral'
            return supervised_side

        return False

    def _set_supported_side(self, supported_side:Literal['Affirmative', 'Negative','']) -> bool:
        """设置主持人支持的方"""
        if supported_side not in ['Affirmative', 'Negative','']:
            raise ValueError(f"Invalid side: {supported_side}. Must be one of ['Affirmative', 'Negative'].")

        self.mod_ans['supported_side'] = supported_side
        return True

    def _is_debate_completed(self, answer: str) -> bool:
        """检查辩论是否结束"""
        # 去除首尾空白，并检查是否以该标记结尾
        cleaned = answer.strip()
        return cleaned == "[[ ## completed ## ]]"

    def _get_debate_side_arguing (self, side: Literal['Affirmative', 'Negative']) -> bool:
        """检查主持人是否已经给出支持方"""
        if side not in ['Affirmative', 'Negative']:
            raise ValueError(f"Invalid side: {side}. Must be one of ['Affirmative', 'Negative'].")
        
        return self.aff_ans if side == 'Affirmative' else self.neg_ans

    
    ## 这里应该改，通过判断supported_side的结果，取supported_side方最后一次内容？？？？？
    def _get_judge_decision(self) -> dict:
        """由裁判评估哪一方更具有说服力"""
        judge_prompt = (self.config['judge_evaluator_prompt']
                        .replace('##debate_topic##', self.config['debate_topic'])
                        .replace('##affirmative_side_arguing##', self.aff_ans)
                        .replace('##negative_side_arguing##', self.neg_ans))
        return self.judge_eval.run(debate_text=judge_prompt)
    
    def _generate_final_answer(self, side: Literal['Affirmative', 'Negative']) -> str:
        """根据胜出方的论点生成最终答案"""

        context = self._get_debate_side_arguing(side)

        answer_prompt = (self.config['final_answer_prompt']
                        .replace('##user_question##', self.config['debate_topic'])
                        .replace('##context##', context))
    
        return self.answer_eval.run(context=answer_prompt)

