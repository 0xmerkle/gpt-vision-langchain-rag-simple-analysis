import os
import dotenv

from langchain.text_splitter import RecursiveCharacterTextSplitter

from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from deck_analysis import vectorstore_mmembd, retriever_mmembd

dotenv.load_dotenv()


def add_documents_to_chroma(file_path):
    try:
        abs_file_path = os.path.abspath(file_path)
        print(f" === Loading text from {abs_file_path } === ")
        loader = TextLoader(abs_file_path)
        documents = loader.load()
        print(f" === Loaded {len(documents)} documents === ")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        docs = text_splitter.split_documents(documents)
        print(f" === Split documents into {len(docs)} chunks === ")
        for doc in docs:
            print(
                f" ------------------------ \n Adding document to vectorstore 🤓:\n  {doc} \n ------------------------ "
            )

        vectorstore_mmembd.add_documents(docs, embedding_function=OpenAIEmbeddings())
        return len(docs)
    except Exception as e:
        print(e)
        raise Exception("Error adding documents to vectorstore")
