import os
import yaml
from typing import TypedDict, Optional
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings

# Load environment variables from .env file
load_dotenv()

# Initialize our LLM from Gemini
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")
# We use a fast, local embedding model for the database to avoid API rate limits/errors
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Initialize Vector DB (Chroma)
# This will save data locally in a folder called 'chroma_db'
vector_store = Chroma(
    collection_name="drive_legal_laws",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# Define the State for our Agent
class GraphState(TypedDict):
    location: str
    query: str
    db_context: Optional[str]
    search_results: Optional[str]
    final_answer: Optional[str]

def check_vector_db(state: GraphState):
    """Node: Checks local ChromaDB for existing data."""
    print(f"[*] Checking Vector DB for location: {state['location']}")
    
    # We do a similarity search in our local database first
    docs = vector_store.similarity_search(state['query'] + " in " + state['location'], k=3)
    
    if docs:
        context = "\n\n".join([doc.page_content for doc in docs])
        print("[*] Found existing data in Vector DB!")
        return {"db_context": context}
    
    print("[*] No existing data found in Vector DB.")
    return {"db_context": None}

def web_search(state: GraphState):
    """Node: Uses DuckDuckGo to search the web and scrape the top results."""
    print(f"[*] Searching web for: {state['location']} traffic laws...")
    
    # Setup DuckDuckGo to look for official government domains
    wrapper = DuckDuckGoSearchAPIWrapper(region="us-en", max_results=2)
    search = DuckDuckGoSearchRun(api_wrapper=wrapper)
    
    # We search specifically for the location and traffic laws on .gov sites
    search_query = f"site:.gov {state['location']} traffic laws violations fine schedule"
    search_string_result = search.invoke(search_query)
    
    print(f"[*] DuckDuckGo returned snippet: {search_string_result[:100]}...")
    
    # Save this new data into our Vector DB so we don't have to search the web next time
    new_doc = Document(page_content=search_string_result, metadata={"location": state['location']})
    vector_store.add_documents([new_doc])
    print("[*] Saved new data to Vector DB!")
    
    return {"search_results": search_string_result}

def generate_response(state: GraphState):
    """Node: Uses Gemini to generate the final response."""
    print("[*] Generating final response with Gemini...")
    
    # We use either the db context or the freshly searched results
    context = state.get("db_context") or state.get("search_results")
    
    with open("prompts.yaml", "r", encoding="utf-8") as f:
        prompts = yaml.safe_load(f)
        
    prompt_template = prompts.get("generate_response")
    prompt = prompt_template.format(
        query=state['query'],
        location=state['location'],
        context=context
    )
    
    response = llm.invoke(prompt)
    return {"final_answer": response.content}

def route_after_db(state: GraphState):
    """Decides where to go after checking the DB."""
    if state.get("db_context"):
        return "generate_response"
    else:
        return "web_search"

# --- Build the Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("check_vector_db", check_vector_db)
workflow.add_node("web_search", web_search)
workflow.add_node("generate_response", generate_response)

workflow.set_entry_point("check_vector_db")
workflow.add_conditional_edges("check_vector_db", route_after_db)
workflow.add_edge("web_search", "generate_response")
workflow.add_edge("generate_response", END)

app_graph = workflow.compile()
