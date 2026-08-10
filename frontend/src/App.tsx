import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

type ResultRow = Record<string, string | number | null>;

type Message =
  | {
      type: "user";
      question: string;
    }
  | {
      type: "assistant";
      question: string;
      answer: string;
      sql: string;
      result: ResultRow[];
      repair_attempts: number;
    }
  | {
      type: "error";
      answer: string;
    };

type AskDBResponse = {
  success?: boolean;
  question?: string;
  answer?: string;
  sql?: string;
  result?: ResultRow[];
  repair_attempts?: number;
  error_type?: string;
  message?: string;
};

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Check whether FastAPI is running
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(
          "http://127.0.0.1:8000/health"
        );

        setBackendOnline(response.ok);
      } catch {
        setBackendOnline(false);
      }
    };

    checkBackend();

    const interval = setInterval(checkBackend, 10000);

    return () => clearInterval(interval);
  }, []);

  // Scroll to latest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  const clearChat = () => {
    setMessages([]);
    setQuestion("");
  };

  const copySQL = async (sql: string, index: number) => {
    try {
      await navigator.clipboard.writeText(sql);

      setCopiedIndex(index);

      setTimeout(() => {
        setCopiedIndex(null);
      }, 1500);
    } catch (error) {
      console.error("Failed to copy SQL:", error);
    }
  };

  const askDatabase = async () => {
    const trimmedQuestion = question.trim();

    if (!trimmedQuestion || loading) {
      return;
    }

    const currentQuestion = trimmedQuestion;

    const conversationContext = messages
      .slice(-6)
      .map((message) => {
        if (message.type === "user") {
          return `User: ${message.question}`;
        }

        if (message.type === "assistant") {
          return `AskDB: ${message.answer}`;
        }

        return "";
      })
      .filter(Boolean)
      .join("\n");

    setMessages((prev) => [
      ...prev,
      {
        type: "user",
        question: currentQuestion,
      },
    ]);

    setQuestion("");
    setLoading(true);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question: currentQuestion,
            conversation_context: conversationContext,
          }),
        }
      );

      if (!response.ok) {
        const errorText = await response.text();

        throw new Error(
          `Request failed with status ${response.status}: ${errorText}`
        );
      }

      const data: AskDBResponse = await response.json();

      if (data.success === false) {
        setBackendOnline(true);

        setMessages((prev) => [
          ...prev,
          {
            type: "error",
            answer:
              data.message ||
              "Could not process your question. Please try again later.",
          },
        ]);

        return;
      }

      setMessages((prev) => [
        ...prev,
        {
          type: "assistant",
          question: data.question || currentQuestion,
          answer: data.answer || "",
          sql: data.sql || "",
          result: data.result || [],
          repair_attempts: data.repair_attempts || 0,
        },
      ]);

      setBackendOnline(true);
    } catch (error) {
      console.error("AskDB request failed:", error);

      setBackendOnline(false);

      setMessages((prev) => [
        ...prev,
        {
          type: "error",
          answer:
            "Could not process your question. Please check that the AskDB backend is running.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (
    event: React.KeyboardEvent<HTMLInputElement>
  ) => {
    if (event.key === "Enter" && !loading) {
      askDatabase();
    }
  };

  return (
    <div className="app">
      <header className="navbar">
        <div className="brand">
          <h2>AskDB</h2>
          <span>Natural Language → SQL</span>
        </div>

        <div className="navbar-actions">
          <div
            className={`status ${
              backendOnline ? "online" : "offline"
            }`}
          >
            <span className="status-dot"></span>

            {backendOnline
              ? "Database Connected"
              : "Backend Offline"}
          </div>

          {messages.length > 0 && (
            <button
              className="clear-button"
              onClick={clearChat}
              disabled={loading}
            >
              Clear Chat
            </button>
          )}
        </div>
      </header>

      <main className="chat-container">
        {messages.length === 0 && (
          <div className="welcome">
            <h1>Ask your database anything.</h1>

            <p>
              Ask questions in plain English and get answers
              directly from your database.
            </p>

            <div className="examples">
              <button
                onClick={() =>
                  setQuestion(
                    "What are the top 5 products by total quantity sold?"
                  )
                }
              >
                Top 5 products
              </button>

              <button
                onClick={() =>
                  setQuestion(
                    "Which city has the highest number of customers?"
                  )
                }
              >
                Top customer city
              </button>

              <button
                onClick={() =>
                  setQuestion(
                    "Which product category generated the highest revenue?"
                  )
                }
              >
                Highest revenue category
              </button>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.type}`}
          >
            {message.type === "user" && (
              <div className="user-message">
                <span>You</span>
                <p>{message.question}</p>
              </div>
            )}

            {message.type === "assistant" && (
              <div className="assistant-message">
                <span>AskDB</span>

                <div className="answer">
                  <ReactMarkdown>
                    {message.answer}
                  </ReactMarkdown>
                </div>

                {message.result.length > 0 && (
                  <div className="table-wrapper">
                    <table>
                      <thead>
                        <tr>
                          {Object.keys(
                            message.result[0]
                          ).map((column) => (
                            <th key={column}>
                              {column}
                            </th>
                          ))}
                        </tr>
                      </thead>

                      <tbody>
                        {message.result.map(
                          (row, rowIndex) => (
                            <tr key={rowIndex}>
                              {Object.values(row).map(
                                (value, colIndex) => (
                                  <td key={colIndex}>
                                    {value === null
                                      ? "NULL"
                                      : String(value)}
                                  </td>
                                )
                              )}
                            </tr>
                          )
                        )}
                      </tbody>
                    </table>
                  </div>
                )}

                <details className="sql-box">
                  <summary>
                    View generated SQL
                  </summary>

                  <div className="sql-content">
                    <button
                      className="copy-button"
                      onClick={() =>
                        copySQL(message.sql, index)
                      }
                    >
                      {copiedIndex === index
                        ? "Copied!"
                        : "Copy SQL"}
                    </button>

                    <pre>{message.sql}</pre>
                  </div>
                </details>

                {message.repair_attempts > 0 && (
                  <div className="repair-info">
                    SQL automatically repaired{" "}
                    {message.repair_attempts} time(s).
                  </div>
                )}
              </div>
            )}

            {message.type === "error" && (
              <div className="error-message">
                {message.answer}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="loading">
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
            <span className="loading-dot"></span>
            <span>Querying database...</span>
          </div>
        )}

        <div ref={bottomRef}></div>
      </main>

      <div className="input-area">
        <div className="input-box">
          <input
            type="text"
            value={question}
            placeholder={
              backendOnline
                ? "Ask a question about your database..."
                : "Backend is offline..."
            }
            onChange={(event) =>
              setQuestion(event.target.value)
            }
            onKeyDown={handleKeyDown}
            disabled={loading || !backendOnline}
          />

          <button
            onClick={askDatabase}
            disabled={
              loading ||
              !question.trim() ||
              !backendOnline
            }
          >
            {loading ? "..." : "Ask"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;