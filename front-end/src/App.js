import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import {
  Container,
  Box,
  Typography,
  Button,
  Paper,
  CircularProgress,
  LinearProgress, // For the progress bar
  Alert,
  styled
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import DownloadIcon from '@mui/icons-material/Download';

const VisuallyHiddenInput = styled('input')({
  clip: 'rect(0 0 0 0)',
  clipPath: 'inset(50%)',
  height: 1,
  overflow: 'hidden',
  position: 'absolute',
  bottom: 0,
  left: 0,
  whiteSpace: 'nowrap',
  width: 1,
});

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [fileNameDisplay, setFileNameDisplay] = useState('No file chosen');

  // New state variables for processing
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(''); // e.g., "pending", "processing", "complete", "error"
  const [taskFileName, setTaskFileName] = useState(''); // To display the name of the file being processed

  const pollingIntervalRef = useRef(null);

    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000'; // API Base URL


  useEffect(() => {
    // Cleanup polling on component unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  const resetState = () => {
    setSelectedFile(null);
    setFileNameDisplay('No file chosen');
    setMessage('');
    setError('');
    setIsUploading(false);
    setTaskId(null);
    setProgress(0);
    setProcessingStatus('');
    setTaskFileName('');
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
     // Visually clear the file input
    const fileInput = document.getElementById('file-upload-input');
    if (fileInput) {
        fileInput.value = '';
    }
  };


  const pollTaskStatus = (currentTaskId) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/status/${currentTaskId}`);
        const taskData = response.data;

        setProgress(taskData.progress || 0);
        setProcessingStatus(taskData.status);
        // setTaskFileName(taskData.original_filename || taskFileName); // Keep original if already set

        if (taskData.status === 'complete' || taskData.status === 'error') {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
          if (taskData.status === 'complete') {
            setMessage(`Processing complete for ${taskData.original_filename || 'file'}. Ready to download.`);
          } else if (taskData.status === 'error') {
            setError(`Processing error for ${taskData.original_filename || 'file'}: ${taskData.error_message || 'Unknown error'}`);
          }
        }
      } catch (err) {
        console.error("Polling error:", err);
        setError('Error fetching processing status. Please try again.');
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
        setProcessingStatus('error'); // Set status to error to stop UI waiting
      }
    }, 2000); // Poll every 2 seconds
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Reset previous task state if a new file is selected
      if (taskId) {
        resetState();
      }
      setSelectedFile(file);
      setFileNameDisplay(file.name);
      setMessage('');
      setError('');
    } else {
      // If selection is cancelled, only clear file-specific state
      setSelectedFile(null);
      setFileNameDisplay('No file chosen');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    setMessage('');
    setError('');
    setIsUploading(true);
    setProgress(0); // Reset progress for new upload
    setProcessingStatus('uploading'); // Initial status
    setTaskFileName(selectedFile.name); // Set filename for display during processing

    try {
      const response = await axios.post(`${API_BASE_URL}/upload/`, formData);
      const { task_id, filename: uploadedFilename, message: uploadMessage } = response.data;

      setTaskId(task_id);
      setTaskFileName(uploadedFilename || selectedFile.name); // Use filename from response if available
      setIsUploading(false); // Upload itself is done
      setProcessingStatus('pending'); // Now waiting for backend processing
      setMessage(uploadMessage || `File '${uploadedFilename}' received. Processing started.`);
      pollTaskStatus(task_id);

    } catch (err) {
      console.error("Upload error:", err);
      let errorMessageText = 'Upload failed. Please try again.';
      if (err.response && err.response.data) {
        if (err.response.data instanceof Blob && err.response.data.type === "application/json") {
          try {
            const errorJsonText = await err.response.data.text();
            const errorJson = JSON.parse(errorJsonText);
            errorMessageText = errorJson.detail || errorJson.message || errorMessageText;
          } catch (parseError) {
            console.error("Error parsing error response:", parseError);
          }
        } else if (typeof err.response.data === 'object' && (err.response.data.detail || err.response.data.message)) {
           errorMessageText = err.response.data.detail || err.response.data.message;
        }
      } else if (err.message) {
        errorMessageText = err.message;
      }
      setError(errorMessageText);
      setIsUploading(false);
      setProcessingStatus('');
      setTaskFileName('');
    }
  };

  const handleDownload = async () => {
    if (!taskId || processingStatus !== 'complete') {
      setError('File is not ready for download or task ID is missing.');
      return;
    }
    setMessage('Preparing download...');
    setError('');
    try {
      const response = await axios.get(`${API_BASE_URL}/download/${taskId}`, {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      let filename = taskFileName || 'downloaded_file'; // Use the stored task filename
      const contentDisposition = response.headers['content-disposition'];
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch && filenameMatch.length > 1) {
          filename = filenameMatch[1];
        }
      }

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();

      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);

      setMessage(`Download started for '${filename}'. You can upload another file.`);
      // Reset for next upload after successful download
      resetState();

    } catch (err) {
      console.error("Download error:", err);
      let errorMessageText = 'Download failed.';
       if (err.response && err.response.data) {
        if (err.response.data instanceof Blob && err.response.data.type === "application/json") {
          try {
            const errorJsonText = await err.response.data.text();
            const errorJson = JSON.parse(errorJsonText);
            errorMessageText = errorJson.detail || errorJson.message || errorMessageText;
          } catch (parseError) { /* ignore */ }
        } else if (typeof err.response.data === 'object' && (err.response.data.detail || err.response.data.message)) {
           errorMessageText = err.response.data.detail || err.response.data.message;
        }
      }
      setError(errorMessageText);
      setMessage('');
    }
  };


  return (
    <Container component="main" maxWidth="sm" sx={{ mt: {xs: 4, md: 8}, mb: 4 }}>
      <Paper elevation={3} sx={{ p: { xs: 2, md: 4 }, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h5" gutterBottom>
          File Processing Service
        </Typography>

        {(!taskId || processingStatus === 'complete' || processingStatus === 'error' || processingStatus === '') && (
          <Box sx={{ mt: 2, mb: 3, width: '100%' }}>
            <Button
              component="label"
              role={undefined}
              variant="outlined"
              tabIndex={-1}
              startIcon={<InsertDriveFileIcon />}
              fullWidth
              sx={{
                justifyContent: 'flex-start', textTransform: 'none',
                color: selectedFile ? 'primary.main' : 'text.secondary',
                borderColor: selectedFile ? 'primary.main' : 'rgba(0, 0, 0, 0.23)',
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', py: 1.5
              }}
              disabled={isUploading || (processingStatus && processingStatus !== 'complete' && processingStatus !== 'error')}
            >
              {fileNameDisplay}
              <VisuallyHiddenInput id="file-upload-input" type="file" onChange={handleFileChange} disabled={isUploading || (processingStatus && processingStatus !== 'complete' && processingStatus !== 'error')} />
            </Button>
          </Box>
        )}

        {processingStatus && processingStatus !== 'complete' && processingStatus !== 'error' && processingStatus !== 'uploading' && (
          <Box sx={{ width: '100%', my: 2 }}>
            <Typography variant="body2" gutterBottom align="center">
              Processing: {taskFileName} ({processingStatus})
            </Typography>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="caption" display="block" gutterBottom align="center">
              {Math.round(progress)}%
            </Typography>
          </Box>
        )}

        {(!taskId || processingStatus === 'complete' || processingStatus === 'error' || processingStatus === '') && (
          <Button
            fullWidth
            variant="contained"
            color="primary"
            onClick={handleUpload}
            disabled={!selectedFile || isUploading || (processingStatus && processingStatus !== 'complete' && processingStatus !== 'error')}
            startIcon={isUploading ? <CircularProgress size={20} color="inherit" /> : <CloudUploadIcon />}
            sx={{ py: 1.5, mb: 2 }}
          >
            {isUploading ? 'Uploading...' : 'Upload and Process File'}
          </Button>
        )}

        {processingStatus === 'complete' && taskId && (
          <Button
            fullWidth
            variant="contained"
            color="success"
            onClick={handleDownload}
            startIcon={<DownloadIcon />}
            sx={{ py: 1.5, mb: 2 }}
          >
            Download Processed File ({taskFileName})
          </Button>
        )}

        {message && (
          <Alert severity="success" sx={{ width: '100%', mt: 2 }}>
            {message}
          </Alert>
        )}
        {error && (
          <Alert severity="error" sx={{ width: '100%', mt: 2 }}>
            {error}
          </Alert>
        )}
      </Paper>
    </Container>
  );
}

export default App;