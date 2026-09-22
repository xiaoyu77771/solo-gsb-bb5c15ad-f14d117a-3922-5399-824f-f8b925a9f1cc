import os
import tempfile

tmp = tempfile.mkdtemp()
os.environ["DATABASE_PATH"] = os.path.join(tmp, "test.db")

from fastapi.testclient import TestClient

from app.main import app

with TestClient(app) as c:
    assert c.get("/api/health").json()["status"] == "ok"
    ev = c.post("/api/events", json={"title": "年会抽签"}).json()
    eid, tok = ev["id"], ev["edit_token"]
    H = {"X-Event-Token": tok}
    assert c.get(f"/api/events/{eid}").status_code == 403
    assert c.get("/api/events/99999", headers=H).status_code == 404

    names = ["Alice", "Bob", "Carol", "Dan"]
    pids = {}
    for n in names:
        r = c.post(f"/api/events/{eid}/participants", json={"name": n}, headers=H)
        assert r.status_code == 201, r.text
        pids[n] = r.json()["id"]
    assert c.post(f"/api/events/{eid}/participants", json={"name": "Alice"}, headers=H).status_code == 409

    A, B, C, D = (pids[n] for n in names)
    assert c.post(f"/api/events/{eid}/constraints", json={"giver_id": A, "receiver_id": B}, headers=H).status_code == 201
    assert c.post(f"/api/events/{eid}/constraints", json={"giver_id": B, "receiver_id": C}, headers=H).status_code == 201
    assert c.post(f"/api/events/{eid}/constraints", json={"giver_id": A, "receiver_id": B}, headers=H).status_code == 409
    assert c.post(f"/api/events/{eid}/constraints", json={"giver_id": A, "receiver_id": A}, headers=H).status_code == 422

    d = c.get(f"/api/events/{eid}", headers=H).json()
    assert all(p["reveal_token"] == "" for p in d["participants"])

    r = c.post(f"/api/events/{eid}/draw", headers=H)
    assert r.status_code == 200, r.text
    assert c.post(f"/api/events/{eid}/draw", headers=H).status_code == 409
    assert c.post(f"/api/events/{eid}/participants", json={"name": "Eve"}, headers=H).status_code == 409

    d = c.get(f"/api/events/{eid}", headers=H).json()
    tokens = {p["id"]: p["reveal_token"] for p in d["participants"]}
    assert all(tokens.values())
    assert all(not p["revealed"] for p in d["participants"])
    assert "recipient" not in d["participants"][0]

    s = c.get(f"/api/reveal/{tokens[A]}").json()
    assert s["drawn"] and not s["revealed"] and s["recipient_name"] is not None
    assert s["recipient_name"] != "Alice" and s["recipient_name"] != "Bob"

    r = c.post(f"/api/reveal/{tokens[A]}")
    assert r.status_code == 200 and r.json()["recipient_name"] != "Bob"
    assert c.post(f"/api/reveal/{tokens[A]}").status_code == 409
    s2 = c.get(f"/api/reveal/{tokens[A]}").json()
    assert s2["revealed"] and s2["recipient_name"] is None

    d = c.get(f"/api/events/{eid}", headers=H).json()
    ap = [p for p in d["participants"] if p["id"] == A][0]
    assert ap["revealed"] and "recipient" not in ap
    assert c.get("/api/reveal/nope").status_code == 404
    print("event flow OK")

with TestClient(app) as c2:
    ev = c2.post("/api/events", json={"title": "x"}).json()
    H2 = {"X-Event-Token": ev["edit_token"]}
    eid2 = ev["id"]
    x = c2.post(f"/api/events/{eid2}/participants", json={"name": "X"}, headers=H2).json()["id"]
    y = c2.post(f"/api/events/{eid2}/participants", json={"name": "Y"}, headers=H2).json()["id"]
    c2.post(f"/api/events/{eid2}/constraints", json={"giver_id": x, "receiver_id": y}, headers=H2)
    c2.post(f"/api/events/{eid2}/constraints", json={"giver_id": y, "receiver_id": x}, headers=H2)
    r = c2.post(f"/api/events/{eid2}/draw", headers=H2)
    assert r.status_code == 422 and "不存在合法抽签方案" in r.json()["detail"]
    d = c2.get(f"/api/events/{eid2}", headers=H2).json()
    assert d["drawn"] is False and all(p["reveal_token"] == "" for p in d["participants"])
    cons = d["constraints"]
    # 2 人互禁时必须移除全部禁配才有解
    for con in cons:
        c2.delete(f"/api/events/{eid2}/constraints/{con['id']}", headers=H2)
    assert c2.post(f"/api/events/{eid2}/draw", headers=H2).status_code == 200
    print("no-solution flow OK")

print("ALL TESTS PASSED")
