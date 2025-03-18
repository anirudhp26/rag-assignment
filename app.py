import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from htmlTemplates import css, bot_template, user_template
from engine.vector_store import WeaviateService
from engine.embed import PDFEmbedder
import logging
import torch
import os
from weaviate.classes.config import Property, DataType
from weaviate.classes.query import MetadataQuery
from weaviate import WeaviateClient
load_dotenv()

torch.classes.__path__ = []
logger = logging.getLogger(__name__)

weaviate_url = os.environ["WEAVIATE_URL"]
weaviate_api_key = os.environ["WEAVIATE_API_KEY"]

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def handle_userinput(user_question: str, embedder: PDFEmbedder, weaviateService: WeaviateClient):
    # Embed the user question
    queryEmbed = embedder.embed_text([user_question])

    # query the embeddings
    query_vector = queryEmbed[0].tolist()

    # get the embeddings from weaviate
    doc = weaviateService.collections.get("pdfs")

    # query the embeddings
    query_results = doc.query.near_vector(near_vector=query_vector, limit=2, return_metadata=MetadataQuery(
        distance=True
    )).objects

    if query_results:
        for i, result in enumerate(query_results):
            st.markdown(bot_template.replace("{{MSG}}", result["properties"]["text"]))
    else:
        st.markdown(bot_template.replace("{{MSG}}", "No documents found"))

def main():
    pdfEmbedder = PDFEmbedder()
    weaviateService = WeaviateService(weaviate_url=weaviate_url, weaviate_api_key=weaviate_api_key).client
    st.set_page_config(page_title="Chat with multiple PDFs",
                       page_icon=":books:")
    st.write(css, unsafe_allow_html=True)

    st.header("Chat with PDFs :books:")
    user_question = st.text_input("Ask a question about documents you uploaded:")
    if user_question:
        handle_userinput(user_question, pdfEmbedder, weaviateService)

    with st.sidebar:
        st.subheader("Your documents...")
        pdf_docs = st.file_uploader(
            "Upload your PDFs here and click on 'Process'", accept_multiple_files=True)
        if st.button("Process"):
            if pdf_docs:
                with st.spinner("Processing"):
                    # get pdf text
                    raw_text = pdfEmbedder.load_pdfs(pdf_docs)

                    # get the text chunks
                    chunks = pdfEmbedder.split_text(raw_text)
                    print(f"Number of text chunks: {len(chunks)}")

                    embeddings = pdfEmbedder.embed_text(chunks)
                    print(f"Embeddings shape: {embeddings.shape}")

                    # store the embeddings in weaviate
                    property = Property(
                        name="text",
                        data_type=DataType.TEXT,
                        skip_vectorization=True
                    )

                    isDocAvailable = weaviateService.collections.exists("pdfs")
                    if not isDocAvailable:
                        weaviateService.collections.create("pdfs", properties=[property])
                    
                    for i, chunk in enumerate(chunks):
                        doc = weaviateService.collections.get("pdfs")
                        uuid = doc.data.insert(vector=embeddings[i].tolist(), properties={"text": chunk})
                        logger.info(f"Document {i} stored with UUID: {uuid}")
                        
                    st.success("Documents processed successfully!")
            else:
                st.error("Please upload a PDF file")

if __name__ == '__main__':
    main()