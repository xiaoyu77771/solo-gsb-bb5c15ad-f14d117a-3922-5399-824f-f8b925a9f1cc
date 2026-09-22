"""完美匹配求解器。

在一个秘密赠礼活动中，每位参与者必须恰好送出一份礼物、收到一份礼物，
且不能抽到自己，也不能命中组织者设定的禁配关系。这等价于在一个
二分图（左侧“送礼者”，右侧“收礼者”，排除自己与禁配对）上寻找一个
完美匹配。

采用带 MRV（最少候选优先）启发的回溯随机搜索：找不到时能在合理时间内
确定无解，找到时返回随机合法匹配。
"""

import random


def find_matching(
    participant_ids: list[int],
    forbidden_pairs: set[tuple[int, int]],
    rng: random.Random | None = None,
) -> dict[int, int] | None:
    """返回 {giver_id: receiver_id}；无解时返回 None（不产生部分结果）。"""
    rng = rng or random.Random()
    n = len(participant_ids)
    if n < 2:
        return None

    ids = set(participant_ids)

    def allowed(giver: int, receiver: int) -> bool:
        return giver != receiver and (giver, receiver) not in forbidden_pairs

    # 每个送礼者的候选收礼者（随机排序，保证结果随机）
    candidates: dict[int, list[int]] = {
        g: [r for r in participant_ids if allowed(g, r)] for g in participant_ids
    }
    for g in participant_ids:
        rng.shuffle(candidates[g])

    # 必要条件：每个人至少有一个候选
    if any(not candidates[g] for g in participant_ids):
        return None

    assignment: dict[int, int] = {}
    used_receivers: set[int] = set()

    def backtrack() -> bool:
        if len(assignment) == n:
            return True

        # MRV：在未分配的送礼者中选择候选（与剩余收礼者求交后）最少的一个
        unassigned = [g for g in participant_ids if g not in assignment]
        giver = min(
            unassigned,
            key=lambda g: sum(1 for r in candidates[g] if r in ids and r not in used_receivers),
        )

        possible = [r for r in candidates[giver] if r not in used_receivers]
        if not possible:
            return False

        for receiver in possible:
            assignment[giver] = receiver
            used_receivers.add(receiver)
            if backtrack():
                return True
            used_receivers.remove(receiver)
            del assignment[giver]
        return False

    if backtrack():
        return dict(assignment)
    return None
