import json
import unittest
from pathlib import Path

import role_behaviours
import role_constraints
from web import api


ROOT = Path(__file__).resolve().parent


class RoleCatalogueIntegrityTests(unittest.TestCase):
    # User-provided FM26 identity names. Behaviour evidence is intentionally not part of this matrix.
    EXPECTED = {
        ("IP", "Winger"): {"인사이드 포워드", "인사이드 윙어", "플레이메이킹 윙어", "윙어", "와이드 포워드"},
        ("OOP", "Winger"): {"인사이드 지향 윙어", "추적형 윙어", "윙어", "측면 지향 윙어"},
        ("IP", "AM"): {"공격형 미드필더", "전진형 플레이메이커", "채널 미드필더", "프리 롤", "세컨드 스트라이커"},
        ("OOP", "AM"): {"공격형 미드필더", "중앙 지향 공격형 미드필더", "추적형 공격형 미드필더"},
        ("IP", "CM"): {"공격형 미드필더", "전진형 플레이메이커", "채널 미드필더", "중앙 미드필더", "미드필드 플레이메이커", "와이드 중앙 미드필더"},
        ("OOP", "CM"): {"중앙 미드필더", "압박형 중앙 미드필더", "스크리닝 중앙 미드필더", "와이드 커버링 중앙 미드필더"},
        ("IP", "Wide Midfield"): {"인사이드 윙어", "플레이메이킹 윙어", "윙어", "와이드 미드필더"},
        ("OOP", "Wide Midfield"): {"측면 지향 와이드 미드필더", "추적형 와이드 미드필더", "와이드 미드필더"},
        ("IP", "DM"): {"박스 투 박스 플레이메이커", "딥라잉 플레이메이커", "박스 투 박스 미드필더", "수비형 미드필더", "하프백"},
        ("OOP", "DM"): {"드롭핑 수비형 미드필더", "수비형 미드필더", "스크리닝 수비형 미드필더"},
        ("IP", "Wing-Back"): {"전진형 윙백", "인사이드 윙백", "플레이메이킹 윙백", "윙백"},
        ("OOP", "Wing-Back"): {"홀딩 윙백", "압박형 윙백", "윙백"},
        ("IP", "Full-Back"): {"풀백", "인사이드 풀백", "플레이메이킹 윙백", "인사이드 윙백", "윙백"},
        ("OOP", "Full-Back"): {"풀백", "홀딩 풀백", "압박형 풀백"},
        ("IP", "Centre-Back"): {"전진형 센터백", "볼 플레잉 센터백", "안정형 센터백", "와이드 센터백", "오버래핑 센터백", "중앙 수비수"},
        ("OOP", "Centre-Back"): {"중앙 수비수", "커버링 센터백", "커버링 와이드 센터백", "스토핑 센터백", "스토핑 와이드 센터백", "와이드 센터백"},
        ("IP", "Goalkeeper"): {"볼 플레잉 골키퍼", "골키퍼", "안정형 골키퍼"},
        ("OOP", "Goalkeeper"): {"골키퍼", "라인 홀딩 키퍼", "스위퍼 키퍼"},
    }

    @classmethod
    def setUpClass(cls):
        cls.catalog = role_constraints.load_role_catalog()

    def test_all_user_verified_role_families_are_represented(self):
        for (phase, family), expected_names in self.EXPECTED.items():
            actual_names = {role["role_name_ko"] for role in self.catalog
                            if role["phase"] == phase and family in role["role_families"]}
            self.assertTrue(expected_names <= actual_names, (phase, family, expected_names - actual_names))

    def test_verified_identity_is_selectable_without_behaviour_semantic_or_ers_coverage(self):
        roles = {row["role_internal_id"]: row for row in api.roles_payload("IP", "ST")["roles"]}
        channel_forward = roles["catalog:ip:fw:chf"]
        self.assertEqual("verified", channel_forward["role_identity_status"])
        self.assertEqual("identity_only", channel_forward["behaviour_coverage"])
        self.assertEqual(2, len(roles))

    def test_selector_does_not_filter_by_semantic_or_ers_coverage(self):
        roles = {row["role_internal_id"] for row in api.roles_payload("IP", "DML")["roles"]}
        self.assertIn("catalog:ip:dm:half-back", roles)

    def test_unresolved_identity_is_not_silently_selectable(self):
        payload = api.roles_payload("IP", "AML")
        selectable = {row["role_internal_id"] for row in payload["roles"]}
        unresolved = {row["role_internal_id"] for row in payload["unresolved_roles"]}
        self.assertNotIn("catalog:ip:winger:pw-legacy-name", selectable)
        self.assertIn("catalog:ip:winger:pw-legacy-name", unresolved)
        self.assertIn("catalog:ip:winger:playmaking-winger", unresolved)

    def test_missing_candidates_never_enter_production_selector(self):
        candidates = json.loads((ROOT / "data" / "missing_role_candidates.json").read_text(encoding="utf-8"))["candidates"]
        selector_names = {row["role_name_ko"] for row in api.roles_payload("IP", "ST")["roles"]}
        self.assertEqual({"requires_identity_verification"}, {row["identity_status"] for row in candidates})
        self.assertTrue(all(row["candidate_name"] not in selector_names for row in candidates))

    def test_ip_oop_phase_separation_is_preserved(self):
        oop = api.roles_payload("OOP", "AML")["roles"]
        self.assertTrue(oop)
        self.assertTrue(all(row["phase"] == "OOP" for row in oop))
        self.assertNotIn("catalog:ip:winger:if", {row["role_internal_id"] for row in oop})

    def test_catalogue_identity_and_behaviour_evidence_remain_separate(self):
        knowledge = role_behaviours.load_knowledge_base()
        resolved = {role["internal_id"]: role for role in role_constraints.resolve_catalog(self.catalog, knowledge)}
        self.assertEqual([], resolved["catalog:ip:fw:chf"]["described_behaviours"])
        self.assertEqual("채널 포워드", resolved["catalog:ip:fw:chf"]["role_name_ko"])


if __name__ == "__main__":
    unittest.main()
