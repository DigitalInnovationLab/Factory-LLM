import os
import fitz  # PyMuPDF
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import shutil
from llama_index.core import Document
from llama_index.core import SimpleDirectoryReader
import json

class PDFTextImageReader(SimpleDirectoryReader):
    """Extended SimpleDirectoryReader that extracts both text and images from PDFs."""
    
    def __init__(
        self,
        input_dir: str = None,
        input_files: List[str] = None,
        image_output_dir: str = "./extracted_images",
        recursive: bool = False,
        required_exts: Optional[List[str]] = None,
        exclude_hidden: bool = True,
        **kwargs: Any,
    ) -> None:
        """Initialize with input directory, image output directory, and SimpleDirectoryReader parameters."""
        self.image_output_dir = image_output_dir
        
        # Create image output directory if it doesn't exist
        os.makedirs(self.image_output_dir, exist_ok=True)
        
        # If required_exts is not provided, only process PDFs
        if required_exts is None:
            required_exts = [".pdf"]
        
        # Initialize parent class
        super().__init__(
            input_dir=input_dir,
            input_files=input_files,
            recursive=recursive,
            required_exts=required_exts,
            exclude_hidden=exclude_hidden,
            **kwargs,
        )
    
    def _extract_images_from_pdf(self, file_path: str,page_num: 1) -> List[str]:
        """Extract images from a PDF file and save them to the image output directory."""
        image_paths = []
        
        try:
            # Open the PDF
            doc = fitz.open(file_path)
            pdf_name = Path(file_path).stem
            
            # Create a subdirectory for this PDF's images
            pdf_image_dir = os.path.join(self.image_output_dir, pdf_name)
            os.makedirs(pdf_image_dir, exist_ok=True)
            
            # Extract images from each page
            # for page_num, page in enumerate(doc,start=page_num-1):
            page = doc[page_num-1]
            image_list = page.get_images(full=True)
            
            for img_idx, img_info in enumerate(image_list):
                xref = img_info[0]  # Get the XREF of the image
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                
                # Get image extension
                image_ext = base_image["ext"]
                
                # Create a filename using a hash of the image content to avoid duplicates
                img_hash = hashlib.md5(image_bytes).hexdigest()
                img_filename = f"page{page_num+1}_img{img_idx+1}_{img_hash}.{image_ext}"
                img_path = os.path.join(pdf_image_dir, img_filename)
                
                # Save the image
                with open(img_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                image_paths.append(img_path)
            
            return image_paths
        
        except Exception as e:
            print(f"Error extracting images from {file_path}: {e}")
            return []
    
    def load_data(self,num_workers: int | None = None) -> List[Document]:
        """Load documents and extract images, storing image paths as metadata."""
        # Use parent class to load documents
        documents = super().load_data(num_workers=num_workers)
        
        for page_num,doc in enumerate(documents):
            if "file_path" in doc.metadata and doc.metadata["file_path"].lower().endswith(".pdf"):
                pdf_path = doc.metadata["file_path"]
                image_paths = self._extract_images_from_pdf(pdf_path,page_num=page_num+1)
                
                # Add image paths to document metadata
                if image_paths:
                    doc.metadata["image_paths"] = json.dumps(image_paths)
        
        return documents