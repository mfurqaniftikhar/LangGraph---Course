from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Literal, Annotated
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain.tools import tool
import requests
import random
import os
import asyncio

load_dotenv()

model=ChatGroq(model='llama-3.1-8b-instant',api_key=os.getenv('GROQ_API_KEY'))


# tools
# search_tool = DuckDuckGoSearchRun(response_format="us-en
search_tool=DuckDuckGoSearchRun(response_format="content")

# secound tool
@tool
def calculator(first_num: float ,secound_num: float, operation: str)-> dict:
    
    """
    
    Perform a basic arithmatic operation on two numbers
    Suppor ted operation add, sub, mul, div
    
    """
    try:
        if operation=="add":
            result = first_num + secound_num
        elif operation =="sub":
            result = first_num - secound_num
        elif operation=="mul":
            result = first_num * secound_num
        elif operation == "div":
            if secound_num == 0:
                return {"error": "Division by zero is not avialable"}
            result = first_num/secound_num
        else:
            return {"error": f"Understand operation '{operation}'"}
        return {"first_num": first_num, "secound_num": secound_num, "operation":operation,"result":result}
    except Exception as e:
        return {"error":str(e)}


# third tool
@tool
def get_stock_price(symbol:str) -> dict:
    """ Ftech latest stock price for a given symbol (e.g. 'AAPL', 'TSLA')
    using Alpha Vantage with API key in the URL
    """
    url = "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=AAPL&apikey=KK4SZ82DO494OTFT"
    r = requests.get(url)
    return r.json()

# make tool list

tools = [get_stock_price, search_tool,calculator]

# Make the llm toll-aware
llm_with_tools = model.bind_tools(tools)


class Chatstate(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]

def build_graph():
    async def chat_node(state:Chatstate):
        """ llm node they may answere or request a tool call."""
        message = state["messages"]
        res =await llm_with_tools.ainvoke(message)
        return {"messages": [res]}
    chat_tool = ToolNode(tools)

    graph = StateGraph(Chatstate)

    # nodes
    graph.add_node("chat_node", chat_node)
    graph.add_node("tools", chat_tool)

    # edges
    graph.add_edge(START, "chat_node")
    graph.add_conditional_edges("chat_node", tools_condition)  # bases on the condition like if and if else
    # graph.add_edge("tools", "chat_node")


    com = graph.compile()
    return com
    # print("Graph compiled successfully ✅")

async def main():
    chatbot = build_graph()
    result =await chatbot.ainvoke({"messages": [AIMessage(content="Hello, can you search for the latest news on AI and also add 45 and 78?")]})
    print(result["messages"][-1].content)
    
if __name__ == "__main__":
    asyncio.run(main())