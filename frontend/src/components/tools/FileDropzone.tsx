import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, Image } from 'lucide-react';
import { clsx } from 'clsx';

interface FileDropzoneProps {
  onFileDrop: (file: File) => void;
  accept?: Record<string, string[]>;
  maxSizeMb?: number;
  disabled?: boolean;
  preview?: string | null;
}

export function FileDropzone({
  onFileDrop,
  accept = { 'image/*': [], 'application/pdf': ['.pdf'] },
  maxSizeMb = 25,
  disabled = false,
  preview = null,
}: FileDropzoneProps) {
  const onDrop = useCallback(
    (files: File[]) => {
      if (files[0]) onFileDrop(files[0]);
    },
    [onFileDrop]
  );

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept,
    maxFiles: 1,
    maxSize: maxSizeMb * 1024 * 1024,
    disabled,
  });

  const rejection = fileRejections[0]?.errors[0];

  return (
    <div className="space-y-2">
      <div
        {...getRootProps()}
        className={clsx(
          'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-10 text-center transition-all duration-200',
          isDragActive
            ? 'border-indigo-500 bg-indigo-500/10'
            : disabled
              ? 'cursor-not-allowed border-gray-700 opacity-50'
              : 'border-gray-700 hover:border-indigo-500/60 hover:bg-indigo-500/5'
        )}
      >
        <input {...getInputProps()} />

        {preview ? (
          <img src={preview} alt="Preview" className="max-h-48 rounded-lg object-contain" />
        ) : (
          <>
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-indigo-500/10">
              <Upload size={24} className="text-indigo-400" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-300">
                {isDragActive ? 'Drop it here…' : 'Drag & drop your file here'}
              </p>
              <p className="mt-1 text-xs text-gray-500">or click to browse</p>
            </div>
            <div className="flex items-center gap-4 text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <Image size={12} /> JPEG, PNG, WebP
              </span>
              <span className="flex items-center gap-1">
                <FileText size={12} /> PDF
              </span>
              <span>Max {maxSizeMb}MB</span>
            </div>
          </>
        )}
      </div>
      {rejection && (
        <p className="text-xs text-red-400">
          {rejection.code === 'file-too-large'
            ? `File exceeds ${maxSizeMb}MB limit`
            : rejection.message}
        </p>
      )}
    </div>
  );
}
