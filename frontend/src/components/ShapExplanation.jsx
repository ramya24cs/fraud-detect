function ShapExplanation({ explanation = [] }) {
  if (!explanation || explanation.length === 0) {
    return (
      <div className="shap-explanation">
        <p>No explanation available.</p>
      </div>
    );
  }

  return (
    <div className="shap-explanation">
      <h3>Top Feature Contributions</h3>

      <div className="shap-list">
        {explanation.map((item, index) => (
          <div className="shap-item" key={item.feature || index}>
            <div className="shap-feature">
              <span>{item.feature}</span>
              <span>{Number(item.value).toFixed(4)}</span>
            </div>

            <div className="shap-bar">
              <div
                className="shap-bar-fill"
                style={{
                  width: `${Math.min(
                    Math.abs(Number(item.value)) * 100,
                    100
                  )}%`,
                }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ShapExplanation;