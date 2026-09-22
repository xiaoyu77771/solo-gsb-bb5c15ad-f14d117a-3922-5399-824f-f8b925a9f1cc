import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, saveEventToken } from "../api.js";

export default function HomePage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [joinId, setJoinId] = useState("");
  const [joinToken, setJoinToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function createEvent(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const ev = await api.createEvent(title.trim() || "秘密赠礼");
      saveEventToken(ev.id, ev.edit_token);
      navigate(`/event/${ev.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function joinEvent(e) {
    e.preventDefault();
    const id = joinId.trim();
    const token = joinToken.trim();
    if (!id || !token) {
      setError("请填写活动编号和组织者令牌");
      return;
    }
    saveEventToken(id, token);
    navigate(`/event/${id}`);
  }

  return (
    <div className="page narrow">
      <h1>🎁 秘密赠礼抽签</h1>
      <p className="subtitle">
        录入参与者与禁配关系，一键完成随机匹配。每人恰好送出、收到一份礼物；
        结果只能通过各自的专属链接揭晓，且只能成功揭晓一次。
      </p>

      <div className="card">
        <h2>发起新活动</h2>
        <form onSubmit={createEvent} className="stack">
          <input
            type="text"
            placeholder="活动名称（可选，如：公司年会）"
            value={title}
            maxLength={120}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button type="submit" disabled={busy}>
            {busy ? "创建中…" : "创建活动"}
          </button>
        </form>
      </div>

      <div className="card">
        <h2>组织者进入已有活动</h2>
        <form onSubmit={joinEvent} className="stack">
          <input
            type="text"
            placeholder="活动编号"
            value={joinId}
            onChange={(e) => setJoinId(e.target.value)}
          />
          <input
            type="text"
            placeholder="组织者令牌（创建活动时获得，请妥善保管）"
            value={joinToken}
            onChange={(e) => setJoinToken(e.target.value)}
          />
          <button type="submit" className="secondary">进入</button>
        </form>
      </div>

      {error && <div className="alert error">{error}</div>}
    </div>
  );
}
