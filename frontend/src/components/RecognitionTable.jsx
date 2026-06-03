export default function RecognitionTable({ rows, stats }) {
  if (!rows || rows.length === 0) {
    return <p className="empty-msg">無辨識結果</p>;
  }

  // Dynamic columns: fixed 4 first, then the rest in original order
  const fixed = ["來源檔名", "維修廠", "估價日期", "牌照號碼"];
  const allKeys = Object.keys(rows[0]);
  const dynamic = allKeys.filter((k) => !fixed.includes(k));
  const columns = [...fixed, ...dynamic];

  const stat = stats?.[0];

  return (
    <div className="recognition-table-wrap">
      {stat && (
        <div className="stats-bar">
          <span>維修廠：<strong>{rows[0]["維修廠"] || "—"}</strong></span>
          <span>估價日期：<strong>{rows[0]["估價日期"] || "—"}</strong></span>
          <span>牌照號碼：<strong>{rows[0]["牌照號碼"] || "—"}</strong></span>
          <span>處理時間：<strong>{stat["處理時間(秒)"]}s</strong></span>
          <span>信心水準：<strong>{stat["信心水準"] || "—"}</strong></span>
        </div>
      )}

      <div className="table-scroll">
        <table className="recognition-table">
          <thead>
            <tr>
              {columns
                .filter((c) => !["來源檔名", "維修廠", "估價日期", "牌照號碼"].includes(c))
                .map((col) => (
                  <th key={col}>{col}</th>
                ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i}>
                {columns
                  .filter((c) => !["來源檔名", "維修廠", "估價日期", "牌照號碼"].includes(c))
                  .map((col) => (
                    <td key={col}>{row[col] ?? ""}</td>
                  ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {stat?.["異常備註"] && (
        <p className="anomaly-note">⚠ {stat["異常備註"]}</p>
      )}
    </div>
  );
}
