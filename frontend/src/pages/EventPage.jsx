import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, loadEventToken, saveEventToken } from "../api.js";

export default function EventPage() {
  const { eventId } = useParams();
  const [token, setToken] = useState(() => loadEventToken(eventId));
  const [tokenInput, setTokenInput] = useState("");
  const [event, setEvent] = useState(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [name, setName] = useState("");
  const [giverId, setGiverId] = useState("");
  const [receiverId, setReceiverId] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!token) return;
    try {
      const data = await api.getEvent(eventId, token);
      setEvent(data);
      setError("");
    } catch (err) {
      setError(err.message);
      setEvent(null);
    }
  }, [eventId, token]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // 抽签后每隔几秒刷新一次揭晓状态（只含“是否已揭晓”，不含结果）
  useEffect(() => {
    if (!event?.drawn) return;
    const timer = setInterval(refresh, 5000);
    return () => clearInterval(timer);
  }, [event?.drawn, refresh]);

  const nameById = useMemo(() => {
    const map = {};
    (event?.participants || []).forEach((p) => (map[p.id] = p.name));
    return map;
  }, [event]);

  async function call(action, okMessage) {
    setError("");
    setNotice("");
    setBusy(true);
    try {
      await action();
      await refresh();
      if (okMessage) setNotice(okMessage);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function addParticipant(e) {
    e.preventDefault();
    const value = name.trim();
    if (!value) return;
    call(async () => {
      await api.addParticipant(eventId, token, value);
      setName("");
    }, `已添加参与者：${value}`);
  }

  function removeParticipant(p) {
    if (!window.confirm(`删除参与者「${p.name}」？与其相关的禁配关系也会一并删除。`)) return;
    call(() => api.deleteParticipant(eventId, token, p.id));
  }

  function addConstraint(e) {
    e.preventDefault();
    if (!giverId || !receiverId || giverId === receiverId) {
      setError("请选择两位不同的参与者");
      return;
    }
    call(async () => {
      await api.addConstraint(eventId, token, Number(giverId), Number(receiverId));
      setGiverId("");
      setReceiverId("");
    }, "已添加禁配关系");
  }

  function removeConstraint(c) {
    call(() => api.deleteConstraint(eventId, token, c.id));
  }

  function runDraw() {
    const n = event.participants.length;
    if (n < 2) {
      setError("至少需要 2 位参与者才能抽签");
      return;
    }
    if (!window.confirm(
      `确认对 ${n} 位参与者发起抽签？\n\n抽签完成后：\n· 参与者与禁配关系将被锁定，不能再修改；\n· 系统生成每人专属揭晓链接；\n· 若当前禁配关系无解，会明确提示且不会产生任何配对。`
    )) {
      return;
    }
    call(async () => {
      try {
        await api.draw(eventId, token);
        setNotice("抽签完成！请将下面的专属链接分别发送给对应参与者。");
      } catch (err) {
        // 无解等错误：明确展示，不产生部分结果
        setError(err.message);
        throw err;
      }
    });
  }

  function copy(text, label) {
    const done = () => setNotice(`${label}已复制到剪贴板`);
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(done).catch(() => fallbackCopy(text, done));
    } else {
      fallbackCopy(text, done);
    }
  }

  function fallbackCopy(text, done) {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    try {
      document.execCommand("copy");
      done();
    } catch {
      window.prompt("请手动复制：", text);
    }
    document.body.removeChild(ta);
  }

  function copyAllLinks() {
    const lines = event.participants.map(
      (p) => `${p.name}：${window.location.origin}/r/${p.reveal_token}`
    );
    copy(lines.join("\n"), "全部揭晓链接");
  }

  if (!token) {
    return (
      <div className="page narrow">
        <h1>组织者验证</h1>
        <p className="subtitle">请输入创建活动时获得的组织者令牌。</p>
        <div className="card">
          <form
            className="stack"
            onSubmit={(e) => {
              e.preventDefault();
              const t = tokenInput.trim();
              if (!t) return;
              saveEventToken(eventId, t);
              setToken(t);
            }}
          >
            <input
              type="text"
              placeholder="组织者令牌"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
            />
            <button type="submit">进入活动</button>
          </form>
        </div>
        <p className="back"><Link to="/">← 返回首页</Link></p>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="page narrow">
        <h1>加载中…</h1>
        {error && <div className="alert error">{error}</div>}
        <p className="back"><Link to="/">← 返回首页</Link></p>
      </div>
    );
  }

  const revealedCount = event.participants.filter((p) => p.revealed).length;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>🎄 {event.title}</h1>
          <p className="meta">活动编号：<code>{event.id}</code></p>
        </div>
        <div>
          {event.drawn ? (
            <span className="badge done">已抽签 · {revealedCount}/{event.participants.length} 已揭晓</span>
          ) : (
            <span className="badge pending">未抽签</span>
          )}
        </div>
      </header>

      {error && <div className="alert error">{error}</div>}
      {notice && <div className="alert ok">{notice}</div>}

      {!event.drawn && (
        <div className="grid">
          <section className="card">
            <h2>① 参与者（{event.participants.length}）</h2>
            <form onSubmit={addParticipant} className="inline-form">
              <input
                type="text"
                placeholder="输入姓名"
                value={name}
                maxLength={120}
                onChange={(e) => setName(e.target.value)}
              />
              <button type="submit" disabled={busy}>添加</button>
            </form>
            <ul className="item-list">
              {event.participants.map((p) => (
                <li key={p.id}>
                  <span>{p.name}</span>
                  <button className="link-danger" onClick={() => removeParticipant(p)} disabled={busy}>
                    删除
                  </button>
                </li>
              ))}
              {event.participants.length === 0 && <li className="empty">还没有参与者</li>}
            </ul>
          </section>

          <section className="card">
            <h2>② 禁配关系（{event.constraints.length}）</h2>
            <p className="hint">禁止「送礼者」给「收礼者」送礼。抽到自己由系统默认禁止，无需添加。</p>
            <form onSubmit={addConstraint} className="stack">
              <select value={giverId} onChange={(e) => setGiverId(e.target.value)}>
                <option value="">送礼者…</option>
                {event.participants.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <span className="arrow">不可以送给 →</span>
              <select value={receiverId} onChange={(e) => setReceiverId(e.target.value)}>
                <option value="">收礼者…</option>
                {event.participants.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              <button type="submit" className="secondary" disabled={busy}>添加禁配</button>
            </form>
            <ul className="item-list">
              {event.constraints.map((c) => (
                <li key={c.id}>
                  <span>
                    {nameById[c.giver_id] || "?"} <b>⊘</b> {nameById[c.receiver_id] || "?"}
                  </span>
                  <button className="link-danger" onClick={() => removeConstraint(c)} disabled={busy}>
                    移除
                  </button>
                </li>
              ))}
              {event.constraints.length === 0 && <li className="empty">暂无禁配关系</li>}
            </ul>
          </section>

          <section className="card full">
            <h2>③ 发起抽签</h2>
            <p className="hint">
              系统将求出一个完整匹配：每人恰好送出一份、收到一份，无人抽到自己，
              且不命中任何禁配关系。若无解会明确提示，且不写入任何结果。
            </p>
            <button className="primary big" onClick={runDraw} disabled={busy || event.participants.length < 2}>
              🎲 开始抽签
            </button>
            {event.participants.length < 2 && <p className="hint">至少需要 2 位参与者</p>}
          </section>
        </div>
      )}

      {event.drawn && (
        <section className="card">
          <h2>专属揭晓链接（一次性）</h2>
          <p className="hint">
            请把每个人的链接单独、私密地发送给本人。每个链接只能成功揭晓一次；
            组织者在此只能看到“是否已揭晓”，看不到任何人抽到了谁。
          </p>
          <div className="copy-all">
            <button className="secondary" onClick={copyAllLinks}>复制全部链接（每人一行）</button>
          </div>
          <ul className="link-list">
            {event.participants.map((p) => {
              const url = `${window.location.origin}/r/${p.reveal_token}`;
              return (
                <li key={p.id} className={p.revealed ? "revealed" : ""}>
                  <div className="link-row">
                    <span className="person">{p.name}</span>
                    <span className={p.revealed ? "reveal-badge done" : "reveal-badge pending"}>
                      {p.revealed
                        ? `已揭晓${p.revealed_at ? " · " + new Date(p.revealed_at).toLocaleString() : ""}`
                        : "尚未揭晓"}
                    </span>
                  </div>
                  <div className="link-row url-row">
                    <code>{url}</code>
                    <button onClick={() => copy(url, `「${p.name}」的链接`)}>复制</button>
                  </div>
                </li>
              );
            })}
          </ul>
        </section>
      )}

      <p className="back"><Link to="/">← 返回首页</Link></p>
    </div>
  );
}
