import React from 'react';
import { useNavigate } from 'react-router-dom';

function HelpModal({ isOpen, onClose }) {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleContact = () => {
    window.location.href = 'mailto:chirag.ravat@ifsca.gov.in?subject=IFSCA IntelliChat Help Request';
    onClose();
  };

  const handleHowTo = () => {
    navigate('/help');
    onClose();
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
      <div className="card p-6 max-w-md w-full animate-fadeIn">
        <h2 className="text-xl font-urbanist font-semibold text-mainText dark:text-white mb-4">Get Help</h2>
        <button
          onClick={handleContact}
          className="block w-full mb-4 bg-primary-blue text-white p-3 rounded-lg hover:bg-secondary-blue transition-colors"
        >
          Contact Developer
        </button>
        <div className="text-center mb-4">
          <img src="/utkarsh-photo.jpg" alt="Utkarsh Mishra (Maharaj)" className="mx-auto mb-6 w-32 h-32 sm:w-40 sm:h-40 md:w-48 md:h-48 lg:w-56 lg:h-56" />
          <p className="text-sm text-primary-gray mt-2">Division of Information and Technology</p>
        </div>
        <button
          onClick={handleHowTo}
          className="block w-full mb-4 bg-green-600 text-white p-3 rounded-lg hover:bg-green-700 transition-colors"
        >
          How to Use
        </button>
        <button
          onClick={onClose}
          className="block w-full bg-error-red text-white p-3 rounded-lg hover:bg-red-700 transition-colors"
        >
          Close
        </button>
      </div>
    </div>
  );
}

export default HelpModal;