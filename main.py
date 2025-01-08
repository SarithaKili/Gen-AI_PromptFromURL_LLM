import os
import streamlit as st
import pickle
import time
from langchain import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import UnstructuredURLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()  # Load environment variables (e.g., OpenAI API key)


# Apply custom CSS for the gradient theme
def apply_custom_css():
    st.markdown(
        """
        <style>
        /* General app background with gradient */
        .stApp {
            background-color: #ffffff;
            color:  #333333;
        }

        /* Sidebar background with gradient */
        section[data-testid="stSidebar"] {
            background: linear-gradient(135deg, #1BCEDF, #5B247A);
            color: #ffffff;
        }

        /* Text styling for headers and inputs */
        .stMarkdown, .stHeader, .stSubheader, .stTextInput > div > label {
            color: #ffffff;
        }

        /* Input boxes styling */
        input, textarea {
            background-color: #ffffff;
            color: #333333;
            border: 1px solid #5B247A;
            border-radius: 5px;
        }

        /* Button styling */
        button[kind="primary"] {
            background-color: #1BCEDF;
            color: #ffffff;
            border: none;
            border-radius: 5px;
        }

        button[kind="primary"]:hover {
            background-color: #5B247A;
        }

        /* Scrollbars */
        ::-webkit-scrollbar {
            width: 10px;
        }
        ::-webkit-scrollbar-thumb {
            background: #5B247A;
            border-radius: 5px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #1BCEDF;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


# Call the function to apply custom CSS
apply_custom_css()

# Title and Sidebar Setup
st.title("PromptFromURL: Research Tool")
st.sidebar.title("Enter URLs")

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i + 1}", placeholder="Enter a URL")
    urls.append(url)

process_url_clicked = st.sidebar.button("🔍 Process URLs")
file_path = "faiss_store_openai.pkl"

# Placeholder for messages
main_placeholder = st.empty()
query_placeholder = st.empty()

# Initialize the LLM
llm = OpenAI(temperature=0.9, max_tokens=500)

# Process URLs when the button is clicked
if process_url_clicked:
    if not any(urls):  # Check if all URLs are empty
        st.sidebar.error("Please enter at least one valid URL!")
    else:
        try:
            main_placeholder.info("Loading and processing URLs... 🚀")
            loader = UnstructuredURLLoader(urls=urls)
            data = loader.load()

            if not data:
                main_placeholder.error("No content found at the provided URLs. Please check the links!")
            else:
                # Split the data
                text_splitter = RecursiveCharacterTextSplitter(
                    separators=['\n\n', '\n', '.', ','],
                    chunk_size=1000
                )
                docs = text_splitter.split_documents(data)
                main_placeholder.info("Splitting text into chunks... ✂️")

                # Create embeddings and save them to FAISS index
                embeddings = OpenAIEmbeddings()
                vectorstore_openai = FAISS.from_documents(docs, embeddings)
                main_placeholder.info("Building embedding vectors... 🔧")
                time.sleep(2)

                # Save the FAISS index to a pickle file
                with open(file_path, "wb") as f:
                    pickle.dump(vectorstore_openai, f)

                main_placeholder.success("URLs processed successfully! 🎉")
        except Exception as e:
            main_placeholder.error(f"An error occurred: {e}")

# Input Query and Display Results
query = query_placeholder.text_input("💡 Ask a Question:")
if query:
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                vectorstore = pickle.load(f)
                chain = RetrievalQAWithSourcesChain.from_llm(
                    llm=llm, retriever=vectorstore.as_retriever()
                )
                result = chain({"question": query}, return_only_outputs=True)

                # Display the answer
                st.header("🔍 Answer")
                st.write(result["answer"])

                # Display the sources
                sources = result.get("sources", "")
                if sources:
                    st.subheader("📚 Sources")
                    for idx, source in enumerate(sources.split("\n"), 1):
                        st.markdown(f"{idx}. {source}")
                else:
                    st.info("No sources available for this query.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("No processed data found. Please process URLs first.")
