'use client';

import React, { ChangeEvent } from 'react';

interface FileUploadProps {
  onFileChange: (file: File | null) => void;
  acceptedFileType?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ 
  onFileChange,
  acceptedFileType = 'application/pdf' 
}) => {
  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    onFileChange(file);
  };

  return (
    <div className="mb-4">
      <label htmlFor="file-upload" className="block text-sm font-medium text-gray-700 mb-1">
        Upload Document
      </label>
      <input
        id="file-upload"
        type="file"
        accept={acceptedFileType}
        onChange={handleFileChange}
        className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none p-2 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />
    </div>
  );
};

export default FileUpload;
