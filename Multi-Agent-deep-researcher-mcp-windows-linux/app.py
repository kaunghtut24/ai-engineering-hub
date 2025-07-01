import streamlit as st
from agents import run_research
import os
import weasyprint
from markdown_it import MarkdownIt
import pyperclip
import json
import requests

# Set up page configuration
st.set_page_config(page_title="🔍 Agentic Deep Researcher", layout="wide")

# --- Persistence --- #

USER_DATA_FILE = "user_data.json"

def save_user_data():
    data = {
        "linkup_api_key": st.session_state.linkup_api_key,
        "selected_model": st.session_state.selected_model,
        "messages": st.session_state.messages,
    }
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# --- Model Selection --- #

@st.cache_data
def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        response.raise_for_status()
        return [model["name"] for model in response.json()["models"]]
    except Exception as e:
        st.error(f"Could not get Ollama models: {e}")
        return ["ollama/qwen3:8b", "ollama/llama2", "ollama/codellama"]

# --- App --- #

# Initialize session state variables
user_data = load_user_data()
st.session_state.linkup_api_key = user_data.get("linkup_api_key", "")
st.session_state.selected_model = user_data.get("selected_model", "ollama/qwen3:8b")
st.session_state.messages = user_data.get("messages", [])

def reset_chat():
    st.session_state.messages = []
    save_user_data()

def to_pdf(html_string):
    return weasyprint.HTML(string=html_string).write_pdf()

# Sidebar: Linkup Configuration with updated logo link
with st.sidebar:
    col1, col2 = st.columns([1, 3])
    with col1:
        st.write("")
        st.image(
            "https://avatars.githubusercontent.com/u/175112039?s=200&v=4", width=65)
    with col2:
        st.header("Linkup Configuration")
        st.write("Deep Web Search")

    st.markdown("[Get your API key](https://app.linkup.so/sign-up)",
                unsafe_allow_html=True)

    linkup_api_key = st.text_input(
        "Enter your Linkup API Key", type="password", value=st.session_state.linkup_api_key)
    if linkup_api_key:
        st.session_state.linkup_api_key = linkup_api_key
        os.environ["LINKUP_API_KEY"] = linkup_api_key
        st.success("API Key stored successfully!")
        save_user_data()

    st.header("Model Selection")
    models = get_ollama_models()
    selected_model_raw = st.selectbox("Select a model", models, index=models.index(st.session_state.selected_model) if st.session_state.selected_model in models else 0)
    if not selected_model_raw.startswith("ollama/"):
        st.session_state.selected_model = f"ollama/{selected_model_raw}"
    else:
        st.session_state.selected_model = selected_model_raw
    save_user_data()

# Main Chat Interface Header with powered by logos from original code links
col1, col2 = st.columns([6, 1])
with col1:
    st.markdown("<h2 style='color: #0066cc;'>🔍 Agentic Deep Researcher</h2>",
                unsafe_allow_html=True)
    powered_by_html = """
    <div style='display: flex; align-items: center; gap: 10px; margin-top: 5px;'>
        <span style='font-size: 20px; color: #666;'>Powered by</span>
        <img src="https://cdn.prod.website-files.com/66cf2bfc3ed15b02da0ca770/66d07240057721394308addd_Logo%20(1).svg" width="80"> 
        <span style='font-size: 20px; color: #666;'>and</span>
        <img src="https://framerusercontent.com/images/wLLGrlJoyqYr9WvgZwzlw91A8U.png?scale-down-to=512" width="100">
    </div>
    """
    st.markdown(powered_by_html, unsafe_allow_html=True)
with col2:
    st.button("Clear ↺", on_click=reset_chat)

# Add spacing between header and chat history
st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Save as PDF",
                    data=to_pdf(MarkdownIt().render(message["content"])),
                    file_name="research_report.pdf",
                    mime="application/pdf",
                )
            with col2:
                if st.button("Copy", key=f"copy_{message['content']}"):
                    pyperclip.copy(message["content"])
                    st.success("Copied to clipboard!")


# Accept user input and process the research query
if prompt := st.chat_input("Ask a question about your documents..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    if not st.session_state.linkup_api_key:
        response = "Please enter your Linkup API Key in the sidebar."
    else:
        with st.spinner("Researching... This may take a moment..."):
            try:
                result = run_research(prompt, st.session_state.selected_model)
                response = result
            except Exception as e:
                response = f"An error occurred: {str(e)}"

    with st.chat_message("assistant"):
        st.markdown(response)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Save as PDF",
                data=to_pdf(MarkdownIt().render(response)),
                file_name="research_report.pdf",
                mime="application/pdf",
            )
        with col2:
            if st.button("Copy", key=f"copy_{response}"):
                pyperclip.copy(response)
                st.success("Copied to clipboard!")

    st.session_state.messages.append(
        {"role": "assistant", "content": response})
    save_user_data()

