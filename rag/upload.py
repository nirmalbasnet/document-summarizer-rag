#!/usr/bin/env python3
"""
File upload handler for RAG document processing.
Handles PDF file uploads, validation, and storage.
"""

import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentUploader:
    """
    Class to handle document upload operations including validation,
    storage, and file management.
    """
    
    ALLOWED_EXTENSIONS = {'.pdf'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB in bytes
    UPLOAD_FOLDER = 'static/documents'
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the DocumentUploader.
        
        Args:
            base_dir (str, optional): Base directory for the project. 
                                    If None, uses the parent directory of this script.
        """
        if base_dir is None:
            # Get the directory containing this script, then go up one level to project root
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = Path(base_dir)
        
        self.upload_dir = self.base_dir / self.UPLOAD_FOLDER
        self._ensure_upload_directory()
    
    def _ensure_upload_directory(self) -> None:
        """
        Create the upload directory if it doesn't exist.
        """
        try:
            self.upload_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Upload directory ensured: {self.upload_dir}")
        except Exception as e:
            logger.error(f"Failed to create upload directory: {e}")
            raise e
    
    def validate_file(self, file: FileStorage) -> Tuple[bool, str]:
        """
        Validate the uploaded file.
        
        Args:
            file (FileStorage): The uploaded file object
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        # Check if file exists
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            return False, f"File type '{file_ext}' not allowed. Only PDF files are accepted."
        
        # Check file size (if we can access it)
        try:
            # Move to the end of the file to get size
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > self.MAX_FILE_SIZE:
                size_mb = file_size / (1024 * 1024)
                max_size_mb = self.MAX_FILE_SIZE / (1024 * 1024)
                return False, f"File size ({size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)"
                
        except Exception as e:
            logger.warning(f"Could not check file size: {e}")
        
        # Check filename for security
        secure_name = secure_filename(file.filename)
        if not secure_name:
            return False, "Invalid filename"
        
        return True, "File is valid"
    
    def save_file(self, file: FileStorage) -> Dict[str, any]:
        """
        Save the uploaded file to the upload directory.
        
        Args:
            file (FileStorage): The uploaded file object
            
        Returns:
            Dict[str, any]: Upload result with success status and details
        """
        try:
            # Validate file
            is_valid, error_message = self.validate_file(file)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_message,
                    'filename': file.filename if file else 'Unknown'
                }
            
            # Generate secude filename
            file_path = self.upload_dir / file.filename
            
            # Save the file
            file.save(str(file_path))
            
            # Get file info
            file_size = file_path.stat().st_size
            relative_path = file_path.relative_to(self.base_dir)
            
            logger.info(f"File uploaded successfully: {file.filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': file.filename,
                'original_filename': file.filename,
                'file_path': str(file_path),
                'relative_path': str(relative_path),
                'file_size': file_size,
                'upload_time': datetime.now().isoformat(),
                'message': 'File uploaded successfully'
            }
            
        except Exception as e:
            logger.error(f"Error saving file {file.filename}: {e}")
            return {
                'success': False,
                'error': f"Failed to save file: {str(e)}",
                'filename': file.filename if file else 'Unknown'
            }
    
    def upload_multiple_files(self, files: List[FileStorage]) -> Dict[str, any]:
        """
        Upload multiple files at once.
        
        Args:
            files (List[FileStorage]): List of uploaded file objects
            
        Returns:
            Dict[str, any]: Upload results for all files
        """
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        for file in files:
            result = self.save_file(file)
            results.append(result)
            
            if result['success']:
                successful_uploads += 1
            else:
                failed_uploads += 1
        
        return {
            'success': failed_uploads == 0,
            'total_files': len(files),
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'results': results,
            'message': f"Uploaded {successful_uploads}/{len(files)} files successfully"
        }
    
    def list_uploaded_files(self) -> List[Dict[str, any]]:
        """
        List all uploaded files in the upload directory.
        
        Returns:
            List[Dict[str, any]]: List of file information
        """
        try:
            files_info = []
            
            if not self.upload_dir.exists():
                return files_info
            
            for file_path in self.upload_dir.glob('*.pdf'):
                try:
                    stat = file_path.stat()
                    
                    # Try to get original filename from metadata (if stored)
                    # For now, use the current filename as original filename
                    original_name = file_path.name
                    
                    files_info.append({
                        'filename': file_path.name,
                        'original_filename': original_name,
                        'file_path': str(file_path),
                        'relative_path': str(file_path.relative_to(self.base_dir)),
                        'file_size': stat.st_size,
                        'size': self._format_file_size(stat.st_size),
                        'upload_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'size_formatted': self._format_file_size(stat.st_size)
                    })
                except Exception as e:
                    logger.warning(f"Error getting info for file {file_path}: {e}")
            
            # Sort by upload time (newest first)
            files_info.sort(key=lambda x: x['upload_time'], reverse=True)
            
            return files_info
            
        except Exception as e:
            logger.error(f"Error listing uploaded files: {e}")
            return []
    
    def delete_file(self, filename: str) -> Dict[str, any]:
        """
        Delete an uploaded file.
        
        Args:
            filename (str): Name of the file to delete
            
        Returns:
            Dict[str, any]: Deletion result
        """
        try:
            file_path = self.upload_dir / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File not found',
                    'filename': filename
                }
            
            file_path.unlink()
            logger.info(f"File deleted successfully: {filename}")
            
            return {
                'success': True,
                'filename': filename,
                'message': 'File deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            return {
                'success': False,
                'error': f"Failed to delete file: {str(e)}",
                'filename': filename
            }
    
    def get_upload_stats(self) -> Dict[str, any]:
        """
        Get statistics about uploaded files.
        
        Returns:
            Dict[str, any]: Upload statistics
        """
        try:
            files_info = self.list_uploaded_files()
            total_files = len(files_info)
            total_size = sum(file_info['file_size'] for file_info in files_info)
            
            return {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_formatted': self._format_file_size(total_size),
                'upload_directory': str(self.upload_dir),
                'allowed_extensions': list(self.ALLOWED_EXTENSIONS),
                'max_file_size': self.MAX_FILE_SIZE,
                'max_file_size_formatted': self._format_file_size(self.MAX_FILE_SIZE)
            }
            
        except Exception as e:
            logger.error(f"Error getting upload stats: {e}")
            return {
                'total_files': 0,
                'total_size': 0,
                'error': str(e)
            }
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes (int): File size in bytes
            
        Returns:
            str: Formatted file size
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        
        return f"{s} {size_names[i]}"


# Convenience functions for direct usage
def upload_file(file: FileStorage) -> Dict[str, any]:
    """
    Convenience function to upload a single file.
    
    Args:
        file (FileStorage): The uploaded file object
        
    Returns:
        Dict[str, any]: Upload result
    """
    uploader = DocumentUploader()
    return uploader.save_file(file)


def upload_files(files: List[FileStorage]) -> Dict[str, any]:
    """
    Convenience function to upload multiple files.
    
    Args:
        files (List[FileStorage]): List of uploaded file objects
        
    Returns:
        Dict[str, any]: Upload results
    """
    uploader = DocumentUploader()
    return uploader.upload_multiple_files(files)


def get_uploaded_files() -> List[Dict[str, any]]:
    """
    Convenience function to get list of uploaded files.
    
    Returns:
        List[Dict[str, any]]: List of file information
    """
    uploader = DocumentUploader()
    return uploader.list_uploaded_files()


def delete_uploaded_file(filename: str) -> Dict[str, any]:
    """
    Convenience function to delete an uploaded file.
    
    Args:
        filename (str): Name of the file to delete
        
    Returns:
        Dict[str, any]: Deletion result
    """
    uploader = DocumentUploader()
    return uploader.delete_file(filename)