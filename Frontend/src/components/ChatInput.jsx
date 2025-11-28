import React from 'react';

function ChatInput({ newMessage, isLoading, setNewMessage, submitNewMessage }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitNewMessage();
    }
  };

  return (
    <div className="flex gap-2 items-center">
      <textarea
        value={newMessage}
        onChange={(e) => setNewMessage(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Please Ask your Query 😊.I’m happy to assist you!"
        className="flex-grow p-3 border border-primary-gray rounded-lg focus:ring-primary-blue dark:bg-primary-dark dark:text-white dark:border-gray-600 transition-colors resize-none"
        rows="2"
        maxLength={500}
        disabled={isLoading}
      />
      <button
        onClick={submitNewMessage}
        disabled={isLoading || !newMessage.trim()}
        className="bg-primary-blue text-white px-6 py-2 rounded-full hover:bg-secondary-blue transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Send
      </button>
    </div>
  );
}

export default ChatInput;