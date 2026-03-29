import os
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

EVAL_MODE = os.getenv("APP_ENV") == "evaluation"
EVAL_MAX_OUTPUT_LENGTH = os.getenv("EVAL_MAX_OUTPUT_LENGTH")
# pylint: disable=line-too-long

NO_INFO = "IMPORTANT: If you can't get the answer from the information you know, say you don't know but still keep the prefix at the beginning."


def get_cot_prompt(
    user_input: str, previous_answer: str = "", final_step: bool = False
) -> List[BaseMessage]:
    """
    Create a cot prompt template
    """
    prompts = []

    if previous_answer != "":
        prompts.append(AIMessage(content=previous_answer))
        approach = f"""1. Reflect and give feedback to your previous attempt to answer the question.
2. Given the question, create an improved plan to answer the question.
3. Generate the output response from the plan. Try to improve on your previous response. {"The final output response (in step 3) must be prefixed with 'Output: '" + (
    f" and must be less than {EVAL_MAX_OUTPUT_LENGTH} characters excluding the prefix." if EVAL_MODE else ""
) if final_step else ""}"""
    else:
        approach = f"""1. Given the question, create a plan to answer the question.
2. Generate the output response from the plan. {"The final output response (in step 2) must be prefixed with 'Output: '" + (
    f" and must be less than {EVAL_MAX_OUTPUT_LENGTH} characters excluding the prefix." if EVAL_MODE else ""
) if final_step else ""}"""

    prompts.append(
        HumanMessage(
            content=f"""<Instruction> Answer the question below by thinking step by step like an expert.</Instruction>
<Approach>
To answer the below question, follow these steps:
{approach}
</Approach>

Question: {user_input}"""
        )
    )

    return prompts


def get_generate_plan_prompt(user_input: str) -> List[HumanMessage]:
    """
    Create a generate plan prompt template
    """
    # generate 1: plan. Phase 0 -> 1
    return [
        HumanMessage(
            content=f"""<Instruction> Given a question below, think step by step like an expert. Then, only write a plan to answer the question without giving the solution to the problem, your plan must be prefixed with "Plan:". {NO_INFO} </Instruction>
Question: {user_input}"""
        )
    ]


def get_generate_solution_prompt(user_input: str, plan: str) -> List[HumanMessage]:
    """
    Create a generate solution prompt template
    """
    # generate 2: solution. Phase 1 -> 2
    return [
        HumanMessage(
            content=f"""<Instruction> Given a question and a plan to answer the question below, generate an answer based on the given plan. You can generate any intermediate reasonings, but the final answer must be prefixed with "Output: " {f" and must be less than {EVAL_MAX_OUTPUT_LENGTH} characters excluding the prefix." if EVAL_MODE else ""}. {NO_INFO} </Instruction>
Question: {user_input}
<Plan>
{plan}
</Plan>"""
        )
    ]


def get_aggregate_plan_prompt(user_input: str, plans: str) -> List[HumanMessage]:
    """
    Create an aggregate plan prompt template
    """
    return [
        HumanMessage(
            content=f"""<Instruction> Given the question below, along with a list of different plans to answer the question, meticulously analyse the advantages and disadvantages from each of the plans like an expert. Then create a new plan by combining the advantages and avoiding disadvantages from each of the given plans. The new plan should not include redundant steps that are not directly related to the original question. Your new plan must be prefixed with "Plan:". {NO_INFO} </Instruction>
Question: {user_input}
{plans}"""
        )
    ]


def get_aggregate_answer_prompt(user_input: str, answers: str) -> List[HumanMessage]:
    """
    Create an aggregate answer prompt template
    """

    return [
        HumanMessage(
            content=f"""<Instruction> Given the question below, along with a list of different answers to the question, meticulously analyse the advantages and disadvantages from each of the answers like an expert. Then create a new answer by combining the advantages and avoiding disadvantages from each of the given answers. The new answer should not include any redundant information that is not directly related to the original question. Your new final answer must be prefixed with "Output: "{f" and must be less than {EVAL_MAX_OUTPUT_LENGTH} characters excluding the prefix." if EVAL_MODE else ""} {NO_INFO} </Instruction>
            <Approach>
To answer the below question, follow these steps:
1. Carefully review the provided context.
2. Focus only on information that is explicitly mentioned or implied within the context.
3. Avoid making assumptions or using any outside knowledge not included in the context.
4. Construct the response by logically deriving it from the context provided.
</Approach>
Question: {user_input}
{answers}"""
        )
    ]


def get_vote_prompt(user_input: str, keyword: str, content: str) -> List[HumanMessage]:
    """
    Create a vote prompt template
    """
    vote_no_info = f"IMPORTANT: If the question does not relate to the information you know, then the best choice must be the one that says it does not know and you have to select that choice. Any {keyword} to the question is irrelevant in this case. "
    return [
        HumanMessage(
            content=f"""<Instruction> Given the question below, along with a list of different {keyword}s to answer the question, meticulously analyse the advantages and disadvantages from each of the {keyword}s like an expert. Then decide which {keyword} is most promising. Conclude in the last line "The best choice is {{s}}", where s the integer id of the {keyword}. {vote_no_info}</Instruction>
Question: {user_input}
{content}"""
        )
    ]
