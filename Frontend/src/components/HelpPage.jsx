import React from 'react';

function HelpPage() {
  return (
    <div className="p-8 bg-white dark:bg-gray-800 dark:text-white min-h-screen">
      <h1 className="text-2xl font-urbanist font-semibold text-mainText dark:text-white mb-4">How to Use IFSCA IntelliChat</h1>
      <ol className="list-decimal pl-6 space-y-2">
        <li>Log in with your credentials on the login page.</li>
        <li>Ask questions related to IFSCA rules, regulations, circulars, or master circulars in the chat input.</li>
        <li>Responses will include sources and confidence scores, structured like official documents.</li>
        <li>If the response takes longer than 1 minute, a timeout message will appear.</li>
        <li>Export your chat history to PDF using the "Save Chat as PDF" button.</li>
        <li>Your session expires in 1 hours; save your work before expiration.</li>
        <li>Toggle dark mode for better visibility in low light.</li>
        <li>For help, click "Get Help" to contact developers or view this guide.</li>
      </ol>
    </div>
  );
}

export default HelpPage;