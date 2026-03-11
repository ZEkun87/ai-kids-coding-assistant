// ChatApp.jsx
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './App.css';

export default function ChatApp() {
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);

  const fetchAnswer = async () => {
    if (!question.trim()) return;
    const newUserMessage = { role: 'user', content: question };
    setChatHistory(prev => [...prev, newUserMessage]);

    setLoading(true);
    setQuestion('');

    try {
      const res = await fetch("/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      const newAIMessage = { role: 'ai', content: data.answer || "暂无回答" };
      setChatHistory(prev => [...prev, newAIMessage]);
    } catch (err) {
      const errorMessage = { role: 'ai', content: "请求失败：" + err.message };
      setChatHistory(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setTimeout(() => {
        const chatContainer = document.getElementById('chat-history');
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, 0);
    }
  };

  const clearHistory = () => {
    if (window.confirm("确定要清空所有对话记录吗？")) {
      setChatHistory([]);
    }
  };

  return (
    <div className="App">
      <h1>AI 少儿编程助手</h1>
      {chatHistory.length > 0 && (
        <button className="clear-btn" onClick={clearHistory} disabled={loading}>
          清空对话记录
        </button>
      )}
      <div id="chat-history" className="chat-history">
        {chatHistory.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-avatar">{msg.role === 'user' ? '👧' : '🤖'}</div>
            <div className="message-content">
              {msg.role === 'ai' ? (
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        <SyntaxHighlighter style={dracula} language={match[1]} PreTag="div" {...props}>
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code style={{ backgroundColor:'#3a3a3a', padding:'2px 6px', borderRadius:'4px', color:'#ff7979', fontFamily:'Consolas, Monaco, monospace' }} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : <p>{msg.content}</p>}
            </div>
          </div>
        ))}
      </div>

      <div className="input-area">
        <textarea value={question} onChange={(e)=>setQuestion(e.target.value)} placeholder="请输入你的问题..." disabled={loading}/>
        <button onClick={fetchAnswer} disabled={loading}>
          {loading ? "思考中... 🤔" : "发送问题"}
        </button>
      </div>
    </div>
  );
}