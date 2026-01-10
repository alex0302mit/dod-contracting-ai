import { useState } from 'react';

export interface DocumentUpload {
  id: string;
  project_document_id: string;
  file_name: string;
  file_path: string;
  file_size: number;
  file_type: string;
  version_number: number;
  uploaded_by: string;
  upload_date: string;
  is_current_version: boolean;
  notes: string | null;
  created_at: string;
  uploader?: {
    name: string;
    email: string;
  };
}

export function useDocumentUploads() {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadDocument = async (
    documentId: string,
    file: File,
    notes?: string
  ): Promise<DocumentUpload> => {
    setUploading(true);
    setUploadProgress(0);

    try {
      // TODO: Implement actual file upload to backend
      // For now, this is a placeholder that creates a metadata record
      // Real implementation would use FormData and multipart/form-data

      const token = localStorage.getItem('auth_token');
      if (!token) throw new Error('User not authenticated');

      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      setUploadProgress(30);

      const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/upload?file_name=${encodeURIComponent(file.name)}&notes=${encodeURIComponent(notes || '')}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        // Note: Real implementation would include file data here
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      setUploadProgress(60);

      const data = await response.json();
      setUploadProgress(100);

      return data.upload;
    } catch (error) {
      console.error('Error uploading document:', error);
      throw error;
    } finally {
      setUploading(false);
      setTimeout(() => setUploadProgress(0), 1000);
    }
  };

  const getDocumentUrl = async (filePath: string): Promise<string> => {
    // Return the file path as-is for now
    // Real implementation would generate signed URL or presigned S3 URL
    const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${API_BASE_URL}${filePath}`;
  };

  const downloadDocument = async (filePath: string, fileName: string) => {
    try {
      const url = await getDocumentUrl(filePath);

      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading document:', error);
      throw error;
    }
  };

  const getUploadHistory = async (documentId: string): Promise<DocumentUpload[]> => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/uploads`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch upload history: ${response.statusText}`);
      }

      const data = await response.json();
      return data.uploads || [];
    } catch (error) {
      console.error('Error fetching upload history:', error);
      throw error;
    }
  };

  const deleteUpload = async (uploadId: string, _filePath: string) => {
    try {
      const token = localStorage.getItem('auth_token');
      const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_BASE_URL}/api/uploads/${uploadId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to delete upload: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error deleting upload:', error);
      throw error;
    }
  };

  return {
    uploading,
    uploadProgress,
    uploadDocument,
    getDocumentUrl,
    downloadDocument,
    getUploadHistory,
    deleteUpload,
  };
}
