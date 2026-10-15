import { useState } from "react";
import { getTransactionAdvice } from "../utils/transactionAdvice";

const QUESTIONS = [
  { id: "next", label: "What should I do next?" },
  { id: "recognized", label: "I recognize this transaction" },
  { id: "unrecognized", label: "I don't recognize this transaction" },
  { id: "email", label: "Was an email sent?" },
];

function TransactionAdviceChatbot({ assessment }) {
  const initialMessage = {
    role: "assistant",
    text: getTransactionAdvice(assessment, "next"),
  };
  const [messages, setMessages] = useState([initialMessage]);

  function ask(question) {
    const selectedQuestion = QUESTIONS.find(
      (item) => item.id === question
    );
    if (!selectedQuestion) return;

    setMessages((current) => [
      ...current,
      { role: "user", text: selectedQuestion.label },
      {
        role: "assistant",
        text: getTransactionAdvice(assessment, question),
      },
    ]);
  }

  return (
    <section
      className="dashboard-card transaction-advice-chat"
      aria-label="Transaction next-step chatbot"
    >
      <h3>Need help deciding what to do next?</h3>
      <div className="transaction-advice-messages" aria-live="polite">
        {messages.map((message, index) => (
          <p
            className={`transaction-advice-message transaction-advice-${message.role}`}
            key={`${message.role}-${index}`}
          >
            {message.text}
          </p>
        ))}
      </div>
      <div className="transaction-advice-questions">
        {QUESTIONS.map((question) => (
          <button
            key={question.id}
            type="button"
            className="transaction-advice-question"
            onClick={() => ask(question.id)}
          >
            {question.label}
          </button>
        ))}
      </div>
    </section>
  );
}

export default TransactionAdviceChatbot;
