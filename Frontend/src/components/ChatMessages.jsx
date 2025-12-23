import React from 'react';
import ReactMarkdown from 'react-markdown';

function ChatMessages({ messages, isLoading }) {
  return (
    <div className="flex flex-col gap-4">
      {messages.map((msg, index) => {
        // Deduplicate sources by file_name (show each PDF only once)
        const uniqueSources = msg.sources
          ? Array.from(
              new Map(msg.sources.map((s) => [s.file_name, s])).values()
            )
          : [];

        return (
          <div
            key={index}
            className={`p-4 rounded-lg max-w-3xl ${
              msg.role === 'user'
                ? 'chat-message-user self-end bg-blue-500 text-white'
                : 'chat-message-assistant self-start bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
            }`}
          >
            <div className="prose dark:prose-invert break-words">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>

            {/* Sources - Deduplicated & No Page Number */}
            {uniqueSources.length > 0 && (
              <div className="mt-3 text-sm text-gray-700 dark:text-gray-300">
                <strong>Sources:</strong>
                {uniqueSources.map((source, i) => {
                  const fileUrl = `${import.meta.env.VITE_API_URL}/api/files/${encodeURIComponent(source.file_name)}`;
                  return (
                    <p key={i} className="ml-2 break-all">
                      -{' '}
                      <a
                        href={fileUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-blue underline hover:text-secondary-blue font-medium"
                      >
                        {source.file_name}
                      </a>
                    </p>
                  );
                })}

                {/* Optional: Keep confidence if you still want it */}
                {msg.confidence != null && (
                  <p className="ml-2 mt-1">
                    <strong>Confidence:</strong>{' '}
                    <span className="font-mono text-primary-blue">
                      {typeof msg.confidence === 'number' ? msg.confidence.toFixed(1) : 'N/A'}
                    </span>
                  </p>
                )}
              </div>
            )}

            {/* Error */}
            {msg.error && (
              <p className="text-red-500 text-xs mt-2">Failed to load response.</p>
            )}
          </div>
        );
      })}

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex justify-center py-4">
          <p className="text-sm text-center text-primary-gray dark:text-gray-300 animate-pulse">
            Thinking...
          </p>
        </div>
      )}
    </div>
  );
}

export default ChatMessages;