// ChatApp.jsx
import { useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';
import './App.css';

export default function ChatApp() {
  const [chatHistory, setChatHistory] = useState([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  const fetchAnswer = async () => {
    if (!question.trim()) return;
    const newUserMessage = { role: 'user', content: question };
    setChatHistory(prev => [...prev, newUserMessage]);

    setLoading(true);
    setQuestion('');

    try {
      const res = await fetch("http://127.0.0.1:8001/api/v1/chat/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          question,
          history: chatHistory.map((msg) => ({ role: msg.role, content: msg.content })),
        }),
      });
      if (!res.ok) throw new Error(res.statusText);
      const data = await res.json();
      const newAIMessage = {
        role: 'ai',
        content: data.answer || "暂无回答",
        intent: data.intent || 'qa',
      };
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

  const triggerImagePick = () => {
    fileInputRef.current?.click();
  };

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setChatHistory(prev => [...prev, { role: 'user', content: `请分析这张代码截图：${file.name}` }]);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("http://127.0.0.1:8001/api/v1/chat/ocr-code-analyze", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      // Only show the analysis result, hide the extracted text
      const content = `${data.analysis || "暂无分析结果"}`;
      setChatHistory(prev => [...prev, { role: 'ai', content, intent: 'code_analysis' }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'ai', content: "图片识别失败：" + err.message, intent: 'code_analysis' }]);
    } finally {
      setLoading(false);
      event.target.value = "";
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,  // Mono
          sampleRate: 16000  // 16kHz
        }
      });

      // Try different MIME types in order of preference
      const mimeTypes = [
        'audio/ogg;codecs=opus',
        'audio/ogg',
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/wav'
      ];

      let selectedMimeType = '';
      for (const mimeType of mimeTypes) {
        if (MediaRecorder.isTypeSupported(mimeType)) {
          selectedMimeType = mimeType;
          break;
        }
      }

      if (!selectedMimeType) {
        selectedMimeType = 'audio/webm'; // Fallback
      }

      console.log('Using MIME type:', selectedMimeType);

      const options = { mimeType: selectedMimeType };
      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: selectedMimeType });
        await sendAudioToBackend(audioBlob, selectedMimeType);

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      alert("无法访问麦克风：" + err.message);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const sendAudioToBackend = async (audioBlob, mimeType) => {
    setLoading(true);
    try {
      // Determine file extension based on MIME type
      let extension = 'webm';
      if (mimeType.includes('ogg')) {
        extension = 'ogg';
      } else if (mimeType.includes('wav')) {
        extension = 'wav';
      } else if (mimeType.includes('webm')) {
        extension = 'webm';
      }

      console.log('Sending audio file with extension:', extension);

      const formData = new FormData();
      formData.append("file", audioBlob, `recording.${extension}`);

      const res = await fetch("http://127.0.0.1:8001/api/v1/chat/speech-to-text", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(await res.text());

      const data = await res.json();
      const recognizedText = data.text;

      // Set the recognized text to the input field
      setQuestion(recognizedText);

      // Add user message showing the voice input
      setChatHistory(prev => [...prev, {
        role: 'user',
        content: `🎤 语音输入：${recognizedText}`
      }]);

    } catch (err) {
      alert("语音识别失败：" + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>少儿编程智能辅导系统</h1>
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
                <>
                  {msg.intent && (
                    <div className={`intent-tag intent-tag-${msg.intent}`}>
                      {msg.intent === 'code_analysis' ? '代码诊断' : '知识问答'}
                    </div>
                  )}
                  <ReactMarkdown
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        return !inline && match ? (
                          <SyntaxHighlighter style={dracula} language={match[1]} PreTag="div" {...props}>
                            {String(children).replace(/\n$/, '')}
                          </SyntaxHighlighter>
                        ) : (
                          <code style={{ backgroundColor: '#3a3a3a', padding: '2px 6px', borderRadius: '4px', color: '#ff7979', fontFamily: 'Consolas, Monaco, monospace' }} {...props}>
                            {children}
                          </code>
                        );
                      }
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </>
              ) : <p>{msg.content}</p>}
            </div>
          </div>
        ))}
      </div>

      <div className="input-area">
        <div className="input-toolbar">
          <button type="button" className="secondary-btn" onClick={triggerImagePick} disabled={loading}>
            上传代码截图
          </button>
          <button
            type="button"
            className={`secondary-btn ${isRecording ? 'recording' : ''}`}
            onClick={isRecording ? stopRecording : startRecording}
            disabled={loading}
          >
            {isRecording ? '⏹️ 停止录音' : '🎤 语音输入'}
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            style={{ display: 'none' }}
          />
        </div>
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              fetchAnswer();
            }
          }}
          placeholder="请输入你的问题... (按回车发送，Shift+回车换行)"
          disabled={loading}
        />
        <button onClick={fetchAnswer} disabled={loading}>
          {loading ? "思考中... 🤔" : "发送问题"}
        </button>
      </div>
    </div>
  );
}