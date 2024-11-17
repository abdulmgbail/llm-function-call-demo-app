import streamlit as st
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_core.tools import tool
import sys




messages = []

prompt = st.text_input("Enter your prompt")

@tool(parse_docstring=True)
def get_disk_usage():
     
    """Retrieves disk usage. Call this whenever you need to know the disk usage, for example when a customer asks "What is the disk usage?"
    Args: None

    Note: View JSON Schema: get_disk_usage.args_schema.schema()

    Returns:
        dict: A dictionary containing disk usage statistics with the following keys:
            - total (str): Total disk space in GB
            - used (str): Used disk space in GB
            - free (str): Free disk space in GB
    """
    path = "/"
    total,used,free = shutil.disk_usage(path)
    gb = 1024*1024*1024

    return {
        "total": f"{ total / gb: .2f} gb",
        "used": f"{ used / gb: .2f} gb",
        "free": f"{ free / gb: .2f} gb"
    }

@tool(parse_docstring=True)
def get_time_in_timezone(timezone_name:str):
    """Returns the current time for a given timezone. Call this whenever you need to know the current time of any timezone, for example when a customer asks "What is the time in Kathmandu?"

    Args:
        timezone_name: IANA timezone name (e.g., 'America/New_York')

    Note: View JSON Schema: get_time_in_timezone.args_schema.schema()


    Returns:
        str: Current time in the specified timezone
    """
    try:
        current_time = datetime.now(ZoneInfo(timezone_name))
        return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except Exception as e:
        return f"Error:Invalid time zone:  {str(e)}"

tools_list = {
    "get_disk_usage": get_disk_usage,
    "get_time_in_timezone": get_time_in_timezone
}

@st.cache_resource
def load_model():
    llm = ChatOllama(model="llama3.1:latest")
    return llm

if prompt:
    
    
    llm = load_model()
    llm_with_tools = llm.bind_tools(list(tools_list.values()))

    messages.append(HumanMessage(content=prompt))
    ai_response = llm_with_tools.invoke(messages)
    messages.append(ai_response)

    if not ai_response.tool_calls:
        
        with st.container(height=500,border=True):
            st.write(ai_response.content)
            sys.exit()
    
    for tool_call in ai_response.tool_calls:
        selected_tool = tools_list.get(tool_call["name"].lower())
        tool_response = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_response,tool_call_id=tool_call["id"]))


    final_response = llm_with_tools.stream(messages)
    with st.container(height=500, border=True):
        st.write_stream(final_response)
