import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api.js";

export default function RevealPage() {
  const { token } = useParams();
  const [status, setStatus] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [revealError, setRevealError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api
      .revealStatus(token)
      .then(setStatus)
      .catch((err) => setLoadError(err.message));
  }, [token]);

  async function reveal() {
    setRevealError("");
    setBusy(true);
    try {
      const result = await api.revealNow(token);
      setStatus(result);
    } catch (err) {
      // 可能是“已被揭晓过”的竞态：刷新状态以展示真实情况
      setRevealError(err.message);
      try {
        setStatus(await api.revealStatus(token));
      } catch {
        /* ignore */
      }
    } finally {
      setBusy(false);
    }
  }

  if (loadError) {
    return (
      <div className="page narrow">
        <div className="card center">
          <h1>链接无效</h1>
          <p className="subtitle">{loadError}</p>
          <p className="hint">请核对你收到的链接是否完整。</p>
        </div>
      </div>
    );
  }

  if (!status) {
    return <div className="page narrow"><h1>加载中…</h1></div>;
  }

  return (
    <div className="page narrow">
      <div className="card center reveal-card">
        <h1>🎁 {status.event_title}</h1>
        <p className="subtitle">你好，<b>{status.name}</b></p>

        {!status.drawn && (
          <>
            <div className="alert info">活动还没有抽签，请耐心等待组织者发起抽签。</div>
            <p className="hint">可稍后重新打开此链接查看。</p>
          </>
        )}

        {status.drawn && !status.revealed && status.recipient_name && (
          <>
            <p className="subtitle">准备好了吗？揭晓后本链接将永久关闭，结果只显示这一次。</p>
            <button className="primary big" onClick={reveal} disabled={busy}>
              {busy ? "揭晓中…" : "🎁 揭晓我要送礼物的人"}
            </button>
            {revealError && <div className="alert error">{revealError}</div>}
          </>
        )}

        {status.drawn && status.revealed && (
          <>
            <div className="result-box">
              <p className="hint">你的礼物要送给</p>
              <p className="recipient">
                {status.recipient_name ? (
                  status.recipient_name
                ) : (
                  <>
                    此链接已经揭晓过，<br />结果不会再次显示
                  </>
                )}
              </p>
            </div>
            {status.recipient_name && (
              <p className="hint">请记住或截图保存——离开本页后无法再次查看。</p>
            )}
            {status.revealed_at && (
              <p className="meta">揭晓时间：{new Date(status.revealed_at).toLocaleString()}</p>
            )}
          </>
        )}
      </div>
      <p className="back center"><Link to="/">秘密赠礼抽签</Link></p>
    </div>
  );
}
