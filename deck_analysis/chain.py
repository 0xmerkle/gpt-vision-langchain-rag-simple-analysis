import dotenv

dotenv.load_dotenv()

from langchain.vectorstores.chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain_core.vectorstores import VectorStoreRetriever
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.prompts.prompt import PromptTemplate
from langchain.schema import AIMessage, HumanMessage
from pathlib import Path
from operator import itemgetter


def get_rag_chain(retriever: VectorStoreRetriever):
    template = """Answer the question based only on the following context:
        <context>
        {context}
        </context>"""
    ANSWER_PROMPT = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            ("user", "{question}"),
        ]
    )
    model = ChatOpenAI(model="gpt-3.5-turbo-1106")
    # print(retriever.get_relevant_documents("purpose of presentation"))
    # Define the RAG pipeline
    chain = (
        {
            "context": retriever,
            "question": RunnablePassthrough(),
        }
        | ANSWER_PROMPT
        | model
        | StrOutputParser()
    )

    return chain


vectorstore_mmembd = Chroma(
    collection_name="chroma-rag-2",
    persist_directory=str(Path(__file__).parent.parent / "chroma_db_text"),
    embedding_function=OpenAIEmbeddings(),
)

# Make retriever
retriever_mmembd = vectorstore_mmembd.as_retriever()
# Create RAG chain
chain = get_rag_chain(retriever_mmembd)


# Add typing for input
class Question(BaseModel):
    __root__: str


chain = chain.with_types(input_type=Question)
