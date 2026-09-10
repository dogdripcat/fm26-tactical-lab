"""Deterministic Korean presentation of existing analysis output only."""
from __future__ import annotations

from typing import Any, Dict

STATE = {"connected": "연결 근거 확인", "weakly_connected": "일부 근거", "unknown": "근거 부족", "structurally_unsupported": "구조적 비지원"}
CHAIN = {"broken_progression_chain": "끊긴 전진 경로", "weak_progression_chain": "약한 전진 경로", "unknown_chain": "미확인 전진 경로"}


def _short_edge(edge: Dict[str, Any]) -> Dict[str, Any]:
    provenance = edge.get("provenance", {})
    return {"from": edge.get("from_node"), "to": edge.get("to_node"), "status": edge.get("status", "unknown"),
            "status_ko": STATE.get(edge.get("status"), "근거 부족"),
            "completeness": provenance.get("evidence_completeness", "evidence_missing"),
            "semantic_ids": provenance.get("semantic_ids", []), "behaviour_ids": provenance.get("behaviour_ids", []),
            "evidence_ids": provenance.get("evidence_ids", [])}


def present(report: Dict[str, Any]) -> Dict[str, Any]:
    connectivity = report.get("connectivity", {})
    edges = [_short_edge(edge) for edge in connectivity.get("edges", [])]
    by_status = {status: [edge for edge in edges if edge["status"] == status] for status in STATE}
    chains = [{"status": item.get("status"), "status_ko": CHAIN.get(item.get("status"), "전진 경로 근거 부족"), "nodes": item.get("nodes", [])}
              for item in connectivity.get("progression_chains", [])]
    suggestions = []
    for item in chains:
        if item["status"] in CHAIN:
            suggestions.append(f"{' → '.join(item['nodes'])} 경로는 {item['status_ko']} 상태입니다.")
    for edge in by_status["structurally_unsupported"]:
        suggestions.append(f"{edge['from']} → {edge['to']} 연결은 구조적 비지원으로 표시됩니다.")
    if not connectivity.get("isolated_nodes"):
        suggestions.append("현재 고립된 포지션은 확인되지 않았습니다.")
    return {
        "summary": [
            "연결 근거 확인 edge가 있습니다." if by_status["connected"] else "연결 근거 확인 edge는 현재 없습니다.",
            "일부 연결은 현재 확보된 FM26 근거만으로 확정하기 어렵습니다." if by_status["unknown"] else "현재 근거 부족 edge는 확인되지 않았습니다.",
            "팀 지침의 전술 효과는 아직 분석 모델에 적용되지 않았습니다.",
        ],
        "connectivity": {"connected": by_status["connected"], "weak": by_status["weakly_connected"], "unknown": by_status["unknown"], "structurally_unsupported": by_status["structurally_unsupported"]},
        "progression": chains,
        "partnerships": {"status": "evidence_not_modelled", "message": "파트너십 분석 — 근거 모델 준비 중"},
        "space_structure": {"status": "evidence_not_modelled", "message": "공간 / 구조 분석 — 현재 근거 부족"},
        "suggestions": suggestions,
        "limitations": ["Connectivity는 현재 IP 역할·포지션 근거만 사용합니다.", "OOP 전술 분석은 제한적입니다.", "Unknown은 나쁜 전술을 뜻하지 않으며 Connected는 전술 품질 점수가 아닙니다."],
    }
