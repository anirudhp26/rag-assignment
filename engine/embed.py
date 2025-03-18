from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import torch
from langchain.text_splitter import CharacterTextSplitter

class PDFEmbedder:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.embedder = SentenceTransformer(model_name)
        self.splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=512,
            chunk_overlap=200,
            length_function=len
        )

    def split_text(self, text: str) -> list[str]:
        return self.splitter.split_text(text)

    def load_pdfs(self, pdf_paths) -> str:
        text = ""
        for pdf in pdf_paths:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def embed_text(self, text: list[str]) -> torch.Tensor:
        return self.embedder.encode(text, convert_to_tensor=True)
