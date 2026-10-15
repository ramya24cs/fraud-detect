function ErrorMessage({ message = "Something went wrong." }) {
  return (
    <div className="error-message">
      <p>{message}</p>
    </div>
  );
}

export default ErrorMessage;