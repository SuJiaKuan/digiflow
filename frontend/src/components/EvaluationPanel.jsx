const MAX_DISPLAY = 50; // per error category

export default function EvaluationPanel({ evaluation }) {
  if (!evaluation) return null;

  if (evaluation.error) {
    return (
      <div className="eval-panel">
        <div className="eval-panel__header">GT 評估結果</div>
        <div className="eval-error">⚠ {evaluation.error}</div>
      </div>
    );
  }

  const { scores, general, data } = evaluation;
  const totalErrors =
    (general?.wrong?.length ?? 0) +
    (general?.missing?.length ?? 0) +
    (general?.extra?.length ?? 0) +
    (data?.wrong?.length ?? 0) +
    (data?.missing?.length ?? 0) +
    (data?.extra?.length ?? 0);

  return (
    <div className="eval-panel">
      <div className="eval-panel__header">GT 評估結果 (FAR)</div>

      {/* Score cards */}
      <div className="eval-scores">
        <ScoreCard
          label="Recall"
          value={scores.recall}
          sub={`C=${scores.C} / G=${scores.G}`}
          color="recall"
        />
        <ScoreCard
          label="Precision"
          value={scores.precision}
          sub={`C=${scores.C} / P=${scores.P}`}
          color="precision"
        />
        <ScoreCard
          label="F1 Score"
          value={scores.f1}
          sub={`(調和平均)`}
          color="f1"
        />
      </div>

      {/* Error breakdown */}
      {totalErrors === 0 ? (
        <div className="eval-perfect">✓ 所有欄位完全符合 GT</div>
      ) : (
        <div className="eval-errors">
          <ErrorSection
            title="General（基本資訊）"
            wrong={general?.wrong}
            missing={general?.missing}
            extra={general?.extra}
            renderWrong={(e, i) => (
              <ErrorRow key={i} type="wrong">
                <span className="err-key">{e.key}</span>
                <span className="err-gt">GT: &ldquo;{e.gt || "（空）"}&rdquo;</span>
                <span className="err-arrow">→</span>
                <span className="err-pred">辨識: &ldquo;{e.pred || "（空）"}&rdquo;</span>
              </ErrorRow>
            )}
            renderMissing={(e, i) => (
              <ErrorRow key={i} type="missing">
                <span className="err-key">{e.key}</span>
                <span className="err-gt">GT: &ldquo;{e.gt || "（空）"}&rdquo;</span>
                <span className="err-label--missing">未辨識</span>
              </ErrorRow>
            )}
            renderExtra={(e, i) => (
              <ErrorRow key={i} type="extra">
                <span className="err-key">{e.key}</span>
                <span className="err-pred">辨識: &ldquo;{e.pred || "（空）"}&rdquo;</span>
                <span className="err-label--extra">多辨識</span>
              </ErrorRow>
            )}
          />

          <ErrorSection
            title="Data（明細列）"
            wrong={data?.wrong}
            missing={data?.missing}
            extra={data?.extra}
            renderWrong={(e, i) => (
              <ErrorRow key={i} type="wrong">
                <span className="err-loc">第 {e.row} 列 / {e.col}</span>
                <span className="err-gt">GT: &ldquo;{e.gt || "（空）"}&rdquo;</span>
                <span className="err-arrow">→</span>
                <span className="err-pred">辨識: &ldquo;{e.pred || "（空）"}&rdquo;</span>
              </ErrorRow>
            )}
            renderMissing={(e, i) => (
              <ErrorRow key={i} type="missing">
                <span className="err-loc">第 {e.row} 列 / {e.col}</span>
                <span className="err-gt">GT: &ldquo;{e.gt || "（空）"}&rdquo;</span>
                <span className="err-label--missing">未辨識</span>
              </ErrorRow>
            )}
            renderExtra={(e, i) => (
              <ErrorRow key={i} type="extra">
                <span className="err-loc">第 {e.row} 列 / {e.col}</span>
                <span className="err-pred">辨識: &ldquo;{e.pred || "（空）"}&rdquo;</span>
                <span className="err-label--extra">多辨識</span>
              </ErrorRow>
            )}
          />
        </div>
      )}
    </div>
  );
}

function ScoreCard({ label, value, sub, color }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className={`eval-score-card eval-score-card--${color}`}>
      <div className="eval-score-card__label">{label}</div>
      <div className="eval-score-card__value">{value.toFixed(1)}%</div>
      <div className="eval-score-card__bar">
        <div
          className="eval-score-card__fill"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="eval-score-card__sub">{sub}</div>
    </div>
  );
}

function ErrorSection({ title, wrong, missing, extra, renderWrong, renderMissing, renderExtra }) {
  const nWrong = wrong?.length ?? 0;
  const nMissing = missing?.length ?? 0;
  const nExtra = extra?.length ?? 0;
  if (nWrong + nMissing + nExtra === 0) return null;

  return (
    <div className="eval-section">
      <div className="eval-section__title">{title}</div>

      {nWrong > 0 && (
        <ErrorGroup
          label={`欄位值錯誤 (${nWrong})`}
          colorClass="err-group--wrong"
          items={wrong}
          renderItem={renderWrong}
        />
      )}
      {nMissing > 0 && (
        <ErrorGroup
          label={`漏辨識 (${nMissing})`}
          colorClass="err-group--missing"
          items={missing}
          renderItem={renderMissing}
        />
      )}
      {nExtra > 0 && (
        <ErrorGroup
          label={`多辨識 (${nExtra})`}
          colorClass="err-group--extra"
          items={extra}
          renderItem={renderExtra}
        />
      )}
    </div>
  );
}

function ErrorGroup({ label, colorClass, items, renderItem }) {
  const shown = items.slice(0, MAX_DISPLAY);
  const overflow = items.length - shown.length;
  return (
    <div className={`err-group ${colorClass}`}>
      <div className="err-group__label">{label}</div>
      <div className="err-group__list">
        {shown.map(renderItem)}
        {overflow > 0 && (
          <div className="err-group__overflow">… 還有 {overflow} 筆</div>
        )}
      </div>
    </div>
  );
}

function ErrorRow({ type, children }) {
  return <div className={`err-row err-row--${type}`}>{children}</div>;
}
