import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import HelpModal from './HelpModal';
import { useAuth } from '../contexts/AuthContext';

function Chatbot() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showTimeoutMessage, setShowTimeoutMessage] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showHelpModal, setShowHelpModal] = useState(false);
  const chatRef = useRef(null);
  let timeoutId = null;

  const hour = new Date().getHours();
  const greeting = hour >= 5 && hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  useEffect(() => {
    const dark = localStorage.getItem('darkMode') === 'true';
    setIsDarkMode(dark);
    document.documentElement.classList.toggle('dark', dark);
  }, []);

  useEffect(() => {
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('darkMode', newMode);
    document.documentElement.classList.toggle('dark', newMode);
  };

  const submitNewMessage = async () => {
    const trimmedMessage = newMessage.trim();
    if (!trimmedMessage || isLoading) return;

    const userMsg = {
      role: 'user',
      content: trimmedMessage,
      timestamp: new Date().toISOString()
    };
    const assistantMsg = {
      role: 'assistant',
      content: '',
      sources: [],
      confidence: null,
      loading: true,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setNewMessage('');
    setError('');
    setIsLoading(true);
    setShowTimeoutMessage(false);

    timeoutId = setTimeout(() => setShowTimeoutMessage(true), 60000);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/api/chat?include_confidence=true`,
        { question: trimmedMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      clearTimeout(timeoutId);
      const { answer, sources, confidence } = response.data;

      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        last.content = answer || 'No response received.';
        last.sources = Array.isArray(sources) ? sources : [];
        last.confidence = typeof confidence === 'number' ? confidence : null;
        last.loading = false;
        return updated;
      });
    } catch (err) {
      clearTimeout(timeoutId);
      const errorMsg = err.response?.data?.detail || err.message;
      setError(`Failed to get response: ${errorMsg}`);
      setMessages(prev => {
        const updated = [...prev];
        const last = updated[updated.length - 1];
        last.loading = false;
        last.error = true;
        last.content = `Error: ${errorMsg}`;
        last.sources = [];
        last.confidence = null;
        return updated;
      });
    } finally {
      setIsLoading(false);
      setShowTimeoutMessage(false);
    }
  };

  const exportToPDF = () => {
    if (!chatRef.current) return;
    html2canvas(chatRef.current, { scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('p', 'mm', 'a4');
      const width = pdf.internal.pageSize.getWidth();
      const height = (canvas.height * width) / canvas.width;
      pdf.addImage(imgData, 'PNG', 0, 0, width, height);
      pdf.save('IFSCA_IntelliChat.pdf');
    });
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white dark:bg-primary-dark shadow-sm p-4 flex justify-between items-center">
        <h1 className="text-xl font-urbanist font-semibold text-mainText dark:text-white">
          IFSCA IntelliChat
        </h1>
        <div className="flex gap-2">
          <button onClick={toggleDarkMode} className="bg-primary-blue text-white px-4 py-2 rounded-full hover:bg-secondary-blue transition-colors">
            {isDarkMode ? 'Light Mode' : 'Dark Mode'}
          </button>
          <button onClick={exportToPDF} className="bg-green-600 text-white px-4 py-2 rounded-full hover:bg-green-700 transition-colors">
            Save as PDF
          </button>
          <button onClick={handleLogout} className="bg-error-red text-white px-4 py-2 rounded-full hover:bg-red-700 transition-colors">
            Logout
          </button>
        </div>
      </header>

      <div className="flex-grow overflow-auto p-6" ref={chatRef}>
        {error && <p className="text-error-red text-sm text-center mb-4 animate-fadeIn">{error}</p>}
        {messages.length === 0 && (
          <div className="card p-6 mx-auto max-w-2xl mt-4 animate-fadeIn">
            <p className="font-urbanist text-primary-blue dark:text-white text-lg">
              <strong>{greeting}, {user?.name || 'Guest'}! How can I assist you today?</strong>
            </p>
          </div>
        )}
        <ChatMessages messages={messages} isLoading={isLoading} />
        {showTimeoutMessage && (
          <p className="text-center text-primary-gray dark:text-gray-300 mt-4 animate-fadeIn">
            There is too much load on me, please excuse me a moment.
          </p>
        )}
      </div>

      <div className="card mx-6 mb-6 p-4 sticky bottom-4 flex flex-col gap-4">
        <ChatInput
          newMessage={newMessage}
          isLoading={isLoading}
          setNewMessage={setNewMessage}
          submitNewMessage={submitNewMessage}
        />
        <div className="flex justify-end">
          <button onClick={() => setShowHelpModal(true)} className="bg-primary-blue text-white px-4 py-2 rounded-full hover:bg-secondary-blue transition-colors">
            Get Help
          </button>
        </div>
      </div>

      <HelpModal isOpen={showHelpModal} onClose={() => setShowHelpModal(false)} />
    </div>
  );
}

export default Chatbot;