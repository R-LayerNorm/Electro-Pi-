import os
import sys
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

# Custom wrapper to bypass broken pip dependencies
class LocalEmbeddings(Embeddings):
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)
    
    def embed_documents(self, texts):
        return self.model.encode(texts).tolist()
    
    def embed_query(self, text):
        return self.model.encode(text).tolist()

# 1. Load Documents
print("Loading documents...")
loader = DirectoryLoader(
    "./documents", 
    glob="**/*.md", 
    loader_cls=TextLoader
)
docs = loader.load()

# 2. Chunk Documents
print("Chunking documents...")
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,
    chunk_overlap=50
)
chunks = text_splitter.split_documents(docs)

# 3. Embed & Store in FAISS (Using local model)
print("Embedding and storing in FAISS...")
embeddings = LocalEmbeddings("all-MiniLM-L6-v2")
vectorstore = FAISS.from_documents(chunks, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

# 4. Setup Local LLM (Using llama.cpp server instead of Ollama)
print("Connecting to local LLM via llama.cpp...")
llm = ChatOpenAI(
    base_url="http://localhost:1235/v1", 
    api_key="not-needed", 
    model="llama-3.2-1b", 
    temperature=0,
    max_tokens=150
)

# 5. Create RAG Prompt with Anti-Hallucination Guard
template = """Use the context below to answer the question. 
If the answer is not in the context, reply exactly: "I do not have enough information to answer this question."

Context:
{context}

Question: {question}
Answer:"""

prompt = ChatPromptTemplate.from_template(template)

# 6. Format documents for the prompt
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 7. Build the Chain
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 8. Test Questions
questions = [
    "How many days of vacation do I get?",
    "What are the internet speed requirements for remote work?",
    "Can I get a refund for a mechanical keyboard with the hardware stipend?"
]

print("\n" + "="*50)
print("RUNNING RAG PIPELINE TESTS")
print("="*50 + "\n")

results = []
for q in questions:
    print(f"Q: {q}")
    
    # DEBUG: Show what FAISS actually retrieved
    retrieved_docs = retriever.invoke(q)
    print("--- RETRIEVED CONTEXT ---")
    for doc in retrieved_docs:
        print(doc.page_content)
    print("--------------------------")
    
    sys.stdout.flush() # Force print to show immediately
    answer = rag_chain.invoke(q)
    print(f"A: {answer}\n")
    results.append({"question": q, "answer": answer})

print("="*50)
print("Test complete.")
