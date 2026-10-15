function EmptyState({ message = "No data available." }) {
  return (
    <div className="empty-state">
      <p>{message}</p>
    </div>
  );
}

export default EmptyState;