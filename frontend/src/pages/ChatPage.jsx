import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, FlaskConical, Sparkles, Trash2 } from 'lucide-react';
import { chatWithAI } from '../utils/api';

export default function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "👋 Hi! I'm the **MoleculeAI Assistant**. I can help you understand:\n\n" +
        "- Molecular properties (LogP, TPSA, QED, etc.)\n" +
        "- Drug discovery concepts\n" +
        "- SMILES notation\n" +
        "- Toxicity predictions\n" +
        "- Lipinski's rules\n\n" +
        "Ask me anything about chemistry or drug discovery!"
    }
  ]);
  const [input, setInput] = useState('');
  const [contextSmiles, setContextSmiles] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const stored = sessionStorage.getItem('currentSmiles');
    if (stored) setContextSmiles(stored);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const history = messages.slice(-10).map(m => ({ role: m.role, content: m.content }));
      const data = await chatWithAI(userMessage, contextSmiles || null, history);

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.reply || 'I could not generate a response.',
        sources: data.sources || [],
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: "Chat cleared! Ask me anything about chemistry or drug discovery.",
    }]);
  };

  return (
    <div className="section">
      <div className="container-narrow">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300 text-sm font-medium mb-4">
            <Bot className="w-4 h-4" />
            AI Assistant
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-surface-900 dark:text-surface-100 mb-3" id="chat-title">
            Chemistry <span className="gradient-text">AI Chat</span>
          </h1>
          <p className="text-surface-500 dark:text-surface-400 max-w-xl mx-auto">
            Ask questions about molecular properties, drug discovery, or get explanations for your analysis results.
          </p>
        </div>

        {/* Context SMILES */}
        {contextSmiles && (
          <div className="card mb-4 py-2 px-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <FlaskConical className="w-4 h-4 text-primary-500" />
              <span className="text-xs text-surface-500 dark:text-surface-400">Molecule context:</span>
              <code className="text-xs font-mono text-primary-600 dark:text-primary-400 truncate max-w-xs">
                {contextSmiles}
              </code>
            </div>
            <button onClick={() => setContextSmiles('')} className="text-xs text-surface-400 hover:text-red-500">
              Remove
            </button>
          </div>
        )}

        {/* Chat Area */}
        <div className="card p-0 overflow-hidden" style={{ height: '60vh', display: 'flex', flexDirection: 'column' }}>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center flex-shrink-0">
                    <Sparkles className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${
                  msg.role === 'user'
                    ? 'bg-primary-500 text-white rounded-br-md'
                    : 'bg-surface-100 dark:bg-surface-800 text-surface-800 dark:text-surface-200 rounded-bl-md'
                }`}>
                  <div className="text-sm whitespace-pre-wrap leading-relaxed"
                    dangerouslySetInnerHTML={{
                      __html: msg.content
                        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                        .replace(/\n/g, '<br/>')
                    }}
                  />
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-surface-200 dark:border-surface-700">
                      <span className="text-xs opacity-60">
                        Source: {msg.sources.join(', ')}
                      </span>
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-indigo-500 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-3 justify-start">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                  <Sparkles className="w-4 h-4 text-white" />
                </div>
                <div className="bg-surface-100 dark:bg-surface-800 rounded-2xl rounded-bl-md px-4 py-3">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-surface-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Bar */}
          <div className="border-t border-surface-200 dark:border-surface-700 p-4">
            <div className="flex gap-3">
              <button onClick={clearChat} className="p-2 text-surface-400 hover:text-red-500 transition-colors" title="Clear chat">
                <Trash2 className="w-5 h-5" />
              </button>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSend()}
                placeholder="Ask about LogP, SMILES, drug discovery, toxicity..."
                className="input-field flex-1 text-sm"
                id="chat-input"
                disabled={loading}
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="btn-primary flex items-center gap-2 text-sm disabled:opacity-50"
                id="chat-send-button"
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
