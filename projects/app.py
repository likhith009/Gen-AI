import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from html_chatbot_template import css, bot_template, user_template


def extract_text(pdf_files):
    """
    Function to extract the text from a PDF file

    Args:
        pdf_file (file): The PDF files to extract the text from

    Returns:
        text (str): The extracted text from the PDF file
    """

    # Initialize the raw text variable
    text = ""

    # Iterate over the documents
    for pdf_file in pdf_files:
        print("[INFO] Extracting text from {}".format(pdf_file.name))

        # Read the PDF file
        pdf_reader = PdfReader(pdf_file)

        # Extract the text from the PDF pages and add it to the raw text variable
        for page in pdf_reader.pages:
            text += page.extract_text()
    
    return text

def get_chunks(text):
    """
    Function to get the chunks of text from the raw text

    Args:
        text (str): The raw text from the PDF file

    Returns:
        chunks (list): The list of chunks of text
    """

    # Initialize the text splitter
    splitter = CharacterTextSplitter(
        separator="\n", # Split the text by new line
        chunk_size=1000, # Split the text into chunks of 1000 characters
        chunk_overlap=200, # Overlap the chunks by 200 characters
        length_function=len # Use the length function to get the length of the text
    )

    # Get the chunks of text
    chunks = splitter.split_text(text)

    return chunks

def get_vectorstore(chunks):
    """
    Function to create avector store for the chunks of text to store the embeddings

    Args:
        chunks (list): The list of chunks of text

    Returns:
        vector_store (FAISS): The vector store for the chunks of text
    """

    # Initialize the embeddings model to get the embeddings for the chunks of text
    embeddings = OpenAIEmbeddings()

    # Create a vector store for the chunks of text embeddings
    # Can use any other online vector store (Elasticsearch, PineCone, etc.)
    vector_store = FAISS.from_texts(texts=chunks, embedding=embeddings)

    return vector_store

def get_conversation_chain(vector_store):
    """
    Function to create a conversation chain for the chat model

    Args:
        vector_store (FAISS): The vector store for the chunks of text
    
    Returns:
        conversation_chain (ConversationRetrievalChain): The conversation chain for the chat model
    """
    
    # Initialize the chat model using Langchain OpenAi API
    # Set the temperature and select the model to use
    # Can replace this with any other chat model (Llama, Falcom, etc.)
    llm = ChatOpenAI(model_name='gpt-3.5-turbo', temperature=0.1)

    # Initialize the chat memory
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    # Create a conversation chain for the chat model
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm, # Chat model
        retriever=vector_store.as_retriever(), # Vector store
        memory=memory, # Chat memory
    )

    return conversation_chain

    """
    Function to generate a quiz using the chat model based on the document

    Returns:
        None
    """

    # Define the prompt for generating a quiz
    quiz_prompt = "Generate a 10 question quiz across various topics mentioned in the document and test the student for comprehensive understanding of the document."

    # Get the response from the chat model for the quiz prompt
    response = st.session_state.conversations({'question': quiz_prompt})

    # Update the chat history with the quiz questions
    st.session_state.chat_history = response['chat_history']

    # Add the quiz questions to the UI
    for i, message in enumerate(st.session_state.chat_history):
        # Display the quiz questions
        st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

def generate_response(user_question):
    """
    Function to generate a response for the user query using the chat model

    Args:
        user_question (str): The user query

    Returns:
        None
    """

    # Backend prompt to fine-tune the user's question without displaying it
    backend_prompt = f"""
    Act as a teacher with 20 years of experience and answer the user question in a way which is easy for a student to understand:
    Question: {user_question}
    """

    # Get the response from the chat model for the fine-tuned backend prompt
    response = st.session_state.conversations({'question': backend_prompt})

    # Update the chat history
    st.session_state.chat_history = response['chat_history']

    # Add the response to the UI
    for i, message in enumerate(st.session_state.chat_history):
        # Check if the message is from the user or the chatbot
        if i % 2 == 0:
            # User message - Display only the user's original question
            st.write(user_template.replace("{{MSG}}", user_question), unsafe_allow_html=True)
        else:
            # Chatbot message
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

def generate_quiz():
    """
    Function to generate a quiz using the chat model based on the document
    """
    # Display the title "Quiz questions" in the UI
    st.write("Quiz questions")

    # Define the prompt for generating a quiz
    quiz_prompt = "Create a set of 10 quiz questions with four multiple-choice answers each, formatted for clarity. Each question should be followed by its answer options listed vertically. Ensure the content covers a broad range of topics from the document to evaluate a comprehensive understanding."

    # Get the response from the chat model for the quiz prompt
    response = st.session_state.conversations({'question': quiz_prompt})

    # Update the chat history with the quiz questions
    st.session_state.chat_history = response['chat_history']

    # Add the quiz questions to the UI
    for i, message in enumerate(st.session_state.chat_history):
        # Display the quiz questions
        if i > 0:  # Skip the first message which is the prompt
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)

## Landing page UI
def run_UI():
    """
    The main UI function to display the UI for the webapp

    Args:
        None

    Returns:
        None
    """

    # Load the environment variables (API keys)
    load_dotenv()

    # Set the page tab title
    st.set_page_config(page_title="IntelliLearn", page_icon="🤖", layout="wide")

    # Add the custom CSS to the UI
    st.write(css, unsafe_allow_html=True)

    # Initialize the session state variables to store the conversations and chat history
    if "conversations" not in st.session_state:
        st.session_state.conversations = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    # Set the page title
    st.header("IntelliLearn: Your personal AI study buddy 🤖")

    # Input text box for user query
    user_question = st.text_input("Upload your data and ask me anything?")

    # Check if the user has entered a query/prompt
    if user_question:
        # Call the function to generate the response
        generate_response(user_question)

    # Sidebar menu
    with st.sidebar:
        st.subheader("Document Uploader")

        # Document uploader
        pdf_files = st.file_uploader("Upload a document you want to chat with", type="pdf", key="upload", accept_multiple_files=True)

        # Process the document after the user clicks the button
        if st.button("Start Chatting ✨"):
            # Add a progress spinner
            with st.spinner("Processing"):
                # Convert the PDF to raw text
                raw_text = extract_text(pdf_files)
                
                # Get the chunks of text
                chunks = get_chunks(raw_text)
                
                # Create a vector store for the chunks of text
                vector_store = get_vectorstore(chunks)

                # Create a conversation chain for the chat model
                st.session_state.conversations = get_conversation_chain(vector_store)
        # Inside the run_UI function, after the "Start Chatting ✨" button
    if st.button("Quiz Me"):
        # Call the function to generate the quiz
        generate_quiz()


# Application entry point
if __name__ == "__main__":
    # Run the UI
    run_UI()