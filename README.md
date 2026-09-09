# FM26 Tactical Lab v0.2

## FMF 읽기 전용 탐색기

```powershell
python fm26lab.py inspect-fmf --file "전술파일.fmf"
python fm26lab.py inspect-fmf --file "전술파일.fmf" --out report.json
python -m unittest -v test_inspect_fmf.py
python fm26lab.py self-test
```

콘솔과 `--out` 파일에 동일한 전체 JSON 보고서를 출력합니다. 출력 파일은 새 파일이어야 하며,
기존 파일, 원본의 하드링크/심볼릭 링크, `.fmf` 출력 경로는 덮어쓰지 않습니다.
이 명령은 SQLite에 접근하지 않습니다. 입력은 바이너리 읽기 모드로만 엽니다.

- 파일 크기, 첫 16바이트(magic bytes 관찰값), 첫 256바이트 hex
- 원본 전체의 연속 ASCII printable 문자열(최소 4바이트)과 0부터 시작하는 바이트 위치
- ZIP 헤더와 중앙 디렉터리 읽기 결과 및 항목 목록(추출/CRC 검증 없음)
- GZIP/ZLIB 헤더와 첫 스트림 검증 결과, 잘림/손상/사전 필요/8 MiB 해제 한도 초과 구분
- 원본 전체의 UTF-8 디코딩 가능 여부와 텍스트 판정, JSON/XML 구문 판정

UTF-8 텍스트는 비어 있지 않고 모든 문자가 출력 가능하거나 탭/줄바꿈이어야 합니다.
UTF-8 BOM은 허용하며, XML의 DTD/엔티티 선언은 파싱하지 않습니다.
압축 내부 텍스트, UTF-16 문자열, 파일 중간에 삽입된 압축 스트림은 탐색하지 않습니다.
GZIP 다중 멤버는 첫 스트림만 검증하고 남은 바이트 수를 보고합니다.
입력 전체와 문자열 목록을 메모리에 보관하므로 매우 큰 파일에는 적합하지 않습니다.
헤더 일치나 일반 형식 판정은 FM26 전술 파일임을 입증하지 않습니다.
전술 구조/역할 ID 해석, FM24/25 변환, DB 전술 자동 등록은 수행하지 않습니다.
실제 FM26 `.fmf` 샘플 검증은 아직 수행하지 않았으며, 테스트는 합성 데이터로 진행했습니다.

UI 없이 **실제로 먼저 작동하도록 만든 백엔드 우선 프로토타입**입니다.

## 현재 되는 것

- 전술 버전 저장 (SQLite)
- 경기 결과 저장
- 최근 N경기 집계
- 4-2-3-1 vs 4-3-3 등 기본 상성 휴리스틱 분석
- 스트라이커 공급 / 중원 상성 / 폭 / 저블록 공략 / 전환 위험 진단
- 전술 A/B 버전 결과 비교
- OpenAI Responses API를 통한 GPT 피드백
- GPT 피드백과 당시 분석 컨텍스트를 DB에 자동 저장

중요: 계산 점수는 FM26 매치엔진의 숨겨진 공식이 아니라, **검증 가능한 규칙을 명시적으로 적용하는 휴리스틱**입니다.
실제 경기 데이터가 쌓이면 다음 버전에서 가중치를 조정할 수 있습니다.

---

## 가장 빠른 실행

Windows에서 Python 3.10+가 설치되어 있다면:

1. 압축 해제
2. `run.bat` 더블클릭
3. 메뉴가 뜨면 정상입니다.

또는 터미널에서:

    python fm26lab.py

최초 실행 시 `data/fm26lab.db`가 자동 생성됩니다.

---

## 샘플 전술 등록

    python fm26lab.py tactic-add --file sample_leicester_4231.json

등록된 전술 확인:

    python fm26lab.py tactic-list

---

## 경기 저장 예시

유벤투스 원정 0-4 예시:

    python fm26lab.py match-add --tactic 1 --opponent Juventus --venue away --opp-formation 433 --opp-block mid --gf 0 --ga 4 --xg-for 0.73 --xg-against 2.23 --shots-for 9 --shots-against 19 --sot-for 0 --sot-against 9 --possession 40 --striker-rating 6.2

최근 경기:

    python fm26lab.py match-list --tactic 1

---

## 전술 진단

    python fm26lab.py analyze --tactic 1 --opp-formation 433 --venue away --opp-block mid --opp-strength stronger

JSON 형태로 다음을 반환합니다.

- overall
- 중앙 전개
- 스트라이커 공급
- 박스 침투
- 폭 확보
- 낮은 블록 공략
- 전환 위협
- 레스트 디펜스
- 압박 구조
- 중원 상성
- 경고
- 최소 수정안
- 최근 경기 집계

---

## GPT 연동

### 1) API 키 설정

Windows CMD:

    setx OPENAI_API_KEY "YOUR_KEY"

설정 후 **새 터미널을 열어야 합니다.**

기본 모델은 `gpt-5.6-luna`입니다.
다른 모델을 쓰고 싶으면:

    setx OPENAI_MODEL "gpt-5.6-sol"

### 2) 질문

    python fm26lab.py gpt --tactic 1 --question "최근 5경기에서 CF가 고립되는 가장 가능성 높은 원인을 분석해줘"

프로그램은 GPT에게 다음을 함께 전달합니다.

- 현재 전술 JSON
- 로컬 계산기의 구조 진단
- 최근 경기 원본 데이터
- 최근 경기 평균
- FM26 전용 분석 규칙

응답은 `feedback` 테이블에 자동 저장됩니다.

---

## 전술 버전 비교

전술 v1과 v2를 각각 다른 tactic ID로 저장한 뒤:

    python fm26lab.py compare --a 1 --b 2 --last 5

이렇게 하면 양쪽 최근 5경기 성과를 비교합니다.

---

## v0.1에서 일부러 안 넣은 것

- GUI
- 자동 스크린샷 인식
- 자동 웹 리서치
- 매치엔진 "승률 예측"
- AI가 계산 가중치를 자동 변경하는 기능
- 설치형 EXE

이유는 **전술 데이터 → 경기 데이터 → 계산 → GPT 피드백 → 기록**의 핵심 루프가 먼저 정상 작동해야 하기 때문입니다.

다음 우선순위:

1. 경기/전술 입력 편하게 만들기
2. 전술 변경 diff 자동 기록
3. 홈/원정/상대 포메이션별 통계
4. 스크린샷 입력
5. 가중치 버전 관리 및 사용자 승인형 보정
6. 마지막에 GUI와 Windows 설치 프로그램

---

## 데이터 파일

SQLite DB:

    data/fm26lab.db

전술/경기/GPT 피드백이 모두 이 파일 하나에 저장됩니다.


---

## v0.2 추가 기능

### 코어 자가진단

인터넷/API 없이 DB, 전술 로딩, 경기 저장, 진단, 집계가 실제로 도는지 확인합니다.

    python fm26lab.py self-test

전부 `[PASS]`가 나오면 핵심 엔진은 정상입니다.

### 전술 복제 + 변경사항 자동 기록

먼저 바꾸고 싶은 항목만 JSON으로 만듭니다. 예:

`change_cf_pw.json`

    {
      "ip_roles": {
        "ST": "CF",
        "AMR": "WF"
      }
    }

기존 전술 1번을 v0.2-test로 복제:

    python fm26lab.py tactic-clone --from-id 1 --version v0.2-test --patch change_cf_pw.json --note "CF + WF test"

변경사항은 `tactic_changes` 테이블에 자동 저장됩니다.

### 버전 차이 보기

    python fm26lab.py tactic-diff --a 1 --b 2

### 변경 이력

    python fm26lab.py change-history

---

## 추천 첫 실행 순서

1. `first_run.bat` 실행
2. SELF TEST가 모두 PASS인지 확인
3. 샘플 전술이 아직 없다면 `quickstart.bat`
4. `run.bat`으로 메뉴 실행


## 사용자 확인 역할 사전

`roles.json`은 phase, position_group, name_ko, name_en, ingame_abbr,
verification, source_note를 보관합니다. 제공된 12개 역할은 IP로 관리하고,
OOP는 확인 목록이 없으므로 전부 unverified입니다. position_group은 앱 내부 분류입니다.
미확인 항목의 명칭/인게임 약어는 null이며 기존 토큰은 legacy_token으로 보존합니다.

호환용 alias: IP의 CF → CFD, WF → WFD, BPGK → BGK.
이는 기존 앱 데이터의 호환 변환이며 옛 토큰을 인게임 약어로 인증하지 않습니다.
사용자 확인에 따라 IP의 CFwd → CHF도 호환 alias로 처리합니다.
기존 DB/JSON은 읽을 때 메모리에서 정규화하며 원본을 일괄 수정하지 않습니다.
신규 저장/복제 시 CHF만 저장합니다. 약어 확인만으로 기존 CFwd 가중치를 활성화하지 않습니다.
기존 DB 행은 수정하지 않으며 신규 저장/복제 시 확인 가능한 alias만 canonical로 저장합니다.
IP/OOP 및 각 포메이션은 독립적으로 유지합니다.

미확인 역할은 역할별 가중치와 조건부 보너스에서 제외하고 경고를 출력합니다.
기존 계산의 중립 기본값은 유지됩니다. 검증된 명칭도 가중치의 정확성을 보증하지 않습니다.
CHF, CB, BGK처럼 활성 프로필이 없는 역할에는 새 가중치를 만들지 않습니다.
FMF ID 연결 및 Attack/Support/Defend Duty 변환은 하지 않습니다.

검증: `python -m unittest discover -v` (16개), `python fm26lab.py self-test`.
Python 배포 시 fm26lab.py와 roles.json을 함께 복사하세요.
EXE 빌드 명령에는 roles.json 포함 옵션을 추가했으며 EXE 빌드는 이번에 실행하지 않았습니다.

## FMF 두 파일 비교

```powershell
python fm26lab.py diff-fmf --a base.fmf --b changed.fmf --label "ST_CFD_to_CHF" --out diff_report.json
```

두 입력은 읽기 전용이며 분석 전후 SHA-256을 비교합니다. 원본과 같은 출력 경로,
하드링크/심볼릭 링크 및 기존 출력 파일은 덮어쓰지 않습니다. DB에 접근하지 않습니다.
크기, 같은 offset 기준 동일/변경 바이트 수와 비율, 연속 변경 구간,
각 구간 ±32바이트 hex 문맥, ASCII 문자열 목록과 차이를 JSON에 기록합니다.
끝 offset은 exclusive입니다. 길이가 다른 경우 긴 파일 길이가 비율의 분모이고,
한쪽에만 존재하는 바이트도 변경으로 계산합니다. 삽입/삭제 재정렬은 하지 않습니다.

내부 Zstandard 표준 프레임 시그니처를 검색하고 프레임 경계를 확인한 뒤 각각 해제합니다.
압축 해제는 `zstdDecompressSync`를 제공하는 Node.js가 필요합니다(Node 24에서 검증).
PATH의 node 또는 환경변수 FM26LAB_NODE로 지정한 실행 파일을 사용합니다.
프레임별 출력 한도 8 MiB, 실행 제한 30초이며 실패·의존성 부재도 보고서에 기록합니다.
여러 프레임은 발견 순서로만 대응시킵니다. 의미상 동일한 블록이라는 보장은 없습니다.
압축 해제 결과에도 byte diff와 문자열 비교를 별도로 적용합니다.

`observed`는 실제 바이트 관측 결과, `unknown_meaning`은 해석하지 않은 의미를 구분합니다.
라벨은 사용자 메모이며 역할 변경의 증거로 사용하지 않습니다. FM 역할 ID를 판정하지 않습니다.
전체 입력을 메모리에 읽으며 문자열은 ASCII 연속 4바이트 이상으로 제한합니다.
추가 모듈 fmf_diff.py도 fm26lab.py와 함께 배포하세요.
검증: 전체 21개 테스트 및 기존 self-test 통과. 서로 다른 실제 FMF 쌍은 아직 제공되지 않았습니다.

## 근거 기반 analyze-tactic

```powershell
python fm26lab.py analyze-tactic --file tactic.json --out analysis.json
python fm26lab.py analyze-tactic --tactic 1 --out analysis.json
python fm26lab.py analyze-tactic --file tactic.json --observations observations.json --out analysis.json
```

파일 입력은 DB를 초기화하지 않습니다. DB 입력도 SQLite mode=ro로 원본을 읽으며
JSON/DB를 정규화 결과로 덮어쓰지 않습니다. 출력은 새 파일만 허용합니다.
배포 시 tactic_analysis.py도 함께 복사하세요.

13개 영역마다 configured_structure(실제 입력 설정; raw_value 보존),
expected_structure(검증된 행동/지침 규칙), observed_structure(출처 있는 경기 관측)를 분리합니다.
현재 검증된 행동 규칙은 없으므로 expected_structure는 unknown입니다.
역할 사전의 name_verified와 behaviour_verified는 독립적이며, 기존 verification은
이전 코드 호환용 명칭 상태입니다. 새 엔진은 기존 ROLE_PROFILES/diagnose 점수를 사용하지 않습니다.

각 영역은 status, confidence, evidence, missing_inputs, match_checks, score:null을 포함합니다.
confidence.level은 none/configuration_only/reported_observations로 근거의 종류와 수를 나타내며
확률이나 전술 품질 점수가 아닙니다. 관측이 없으면 insufficient_evidence입니다.
관측이 있더라도 observations_available은 효과·위험이 입증되었다는 뜻이 아닙니다.
expected_effect와 risks는 근거가 없는 동안 unknown으로 유지합니다.

IP/OOP 공통 team_instructions는 국면·인게임 의미를 추측하지 않고
unassigned_configuration에 보존합니다. ip_team_instructions/oop_team_instructions는
설정 사실로 기록하지만 그 효과를 추정하지 않습니다. missing/null/문자열 unknown은
추정값으로 보충하지 않습니다. 분석용 영역명과 경기 확인 항목은 인게임 메뉴명 주장과 구분합니다.

관측 파일은 다음 형식의 배열입니다. 실제 경기에서 확인한 값만 입력하세요.
area는 보고서의 area ID, phase는 해당 영역의 IP/OOP와 일치해야 합니다.

```json
[
  {
    "area": "box_entries",
    "phase": "IP",
    "match_id": "사용자가 식별한 경기",
    "source": "사용자가 확인한 경기 장면의 출처",
    "metric": "박스 진입 인원",
    "value": "unknown"
  }
]
```

unknown 관측은 실제 관측 사실로 집계하지 않습니다. 사용자가 제공한 관측은 독립 검증된
사실로 인증하지 않습니다. 기존 경기 요약 통계만으로 패스 경로·공간 배치를 만들어내지 않습니다.
GPT용 explanation_context(report)는 별도 함수이며 네트워크를 호출하지 않습니다.
이번 analyze-tactic CLI는 결정론적 JSON 보고서까지 제공하며 GPT 설명 자동 호출은 하지 않습니다.
전체 검증: 27개 테스트 및 기존 self-test 통과.

## 역할 행동 지식베이스 — 구조만 제공

role_behaviours.json에는 이름이 확인된 12개 IP 역할의 빈 항목만 있습니다.
각 항목: role, phase, behaviours:[], relationships:[], evidence:[], behaviour_verified:false.
OOP 역할이나 실제 행동 내용은 추가하지 않았습니다.

role_behaviours.py의 load_knowledge_base/validate_knowledge_base가 타입, 중복 ID,
근거 참조와 날짜를 검증합니다. behaviour 필드는 behaviour_id, category, claim,
conditions(객체 배열), evidence_ids, verification(verified/unverified/rejected)입니다.
category는 position_occupancy, ball_receiving, runs, link_play, dribbling, passing,
goal_threat, width, defensive_transition을 지원하지만 역할별 배정은 없습니다.
evidence에는 evidence_id와 source_type, title, source, accessed(YYYY-MM-DD), notes가 필요합니다.
근거가 없는 행동이나 존재하지 않는 evidence_id를 참조하는 행동은 거부합니다.
근거의 존재만으로 검증 상태를 자동 승격하지 않습니다.

roles.json은 명칭 검증을 담당합니다. 그 파일의 behaviour_verified는 이전 형식 호환용이며,
새 분석의 행동 검증은 별도 지식베이스에서 확인합니다. verified_behaviours는
역할의 behaviour_verified가 true이고 개별 행동 verification도 verified일 때만 반환합니다.
역할 활성화는 모든 행동의 일괄 인증이 아닙니다. IP/OOP를 별도 키로 조회합니다.
relationships와 conditions는 데이터 구조만 보존하며 실행하거나 효과를 해석하지 않습니다.

이번 버전에는 행동을 분석 영역으로 변환하는 규칙이 없으므로 expected_structure는 계속
unknown입니다. 시험용 TEST_ONLY 자료는 테스트 안에만 있고 실제 FM 역할 주장이 아닙니다.
배포 시 role_behaviours.py 및 role_behaviours.json도 함께 복사하세요.
EXE 설정에 데이터 포함 옵션을 추가했지만 EXE 빌드는 실행하지 않았습니다.
검증: 기존 27개 + 지식베이스 5개 = 32개 전체 테스트 및 self-test 통과.

## 공식 CFD/WFD 근거 반영 (2026-09-07)

위의 '빈 지식베이스/예상 구조 항상 unknown' 설명은 최초 구조 버전의 기록입니다.
현재 CFD와 WFD에만 공식 근거를 추가했습니다. 다른 역할 및 roles.json은 변경하지 않았습니다.
CFD 6개: 역할 분류, 주 득점원 선택 정보, 핵심 능력치 4개(각각 독립 항목).
WFD 6개: 하이브리드 분류, 폭 유지, 수비 뒤 침투, 득점 우선, 크로스 마무리를 위한 박스 진입, 중앙 연계.
role_classification/key_attribute는 실제 공간 이동 행동과 구분하는 category입니다.

verification=official은 공식 출처를 직접 확인한 개별 항목에 사용합니다.
기존 verified/unverified/rejected도 호환되며, conditions는 객체 또는 문자열 배열을 지원합니다.
현재 공식 항목은 ['in_possession'] 조건입니다. 출처 존재만으로 자동 검증하지 않습니다.
behaviour_verified=true는 등록된 검증 항목의 사용을 허용하는 상태이며 역할의 모든 행동을
알거나 미검증 항목까지 인증한다는 뜻이 아닙니다. 개별 verification도 계속 검사합니다.

analyze-tactic의 role_knowledge에 분류/능력치를 포함한 근거 항목을 제공합니다.
WFD의 명시적으로 연결한 official 행동만 expected_structure에 나타납니다.
해당 영역은 expected_structure_available / confidence.level=official_role_description이며,
이 상태는 경기에서 행동이 발생했다는 의미가 아닙니다. observed_structure는 경기 자료만 사용합니다.
박스 침투는 정성적 역할 설명만 제공하고 인원수, 빈도, 성공률은 계산하지 않습니다.
조건이 추가되어 충족 여부를 확인할 수 없으면 예상 구조 생성을 차단합니다.
CFD 정보는 공간 이동 규칙에 연결하지 않습니다. OOP와 역할 궁합 규칙도 추가하지 않았습니다.

공식 근거(각 항목에 evidence_ids와 URL, 접근일, 해당 절을 기록):
- https://www.footballmanager.com/the-dugout/dominate-dual-strikers-fm26
- https://www.footballmanager.com/the-dugout/leading-line-fm26-lone-strikers
- https://www.footballmanager.com/ko/the-dugout/fm26ui-waideu-powodeu-maseuteohaneun-beob

검증: 전체 37개 테스트와 기존 self-test 통과.

## 사용자 제공 AM/IF 인게임 설명 반영

AM/IF 각각 태그 2개(role_classification)와 행동 3개를 개별 등록했습니다.
근거는 user_ingame_capture, 개별 검증은 user_ingame_verified입니다.
이번 근거는 사용자가 대화에 제공한 인게임 텍스트 전사이며 이미지를 직접 검토했다는 뜻이 아닙니다.
다른 버전 설명이나 애니메이션 해석은 추가하지 않았습니다.
IF의 '더욱 앞으로 전진하라'는 player_instructions에 별도 기록했습니다.
이는 설명 화면에서 확인된 지침이며 현재 분석하는 전술에 실제 활성화됐다고 가정하지 않습니다.

AM/IF의 개별 행동만 예상 구조에 연결합니다. 태그로부터 추가 움직임을 추론하지 않습니다.
AM의 기회 생성은 중앙 공격 전개에 대한 정성적 설명이며 박스 침투나 특정 스트라이커 공급을 보장하지 않습니다.
IF가 풀백에게 공간을 열어준다는 설명도 실제 오버랩 발생·풀백 배치의 증거는 아닙니다.
예상 구조에는 경기 관측을 자동 생성하지 않으며 IF+AM 공간 충돌 규칙은 없습니다.
CFD/WFD를 포함한 다른 역할 데이터는 변경하지 않았습니다.
검증: 전체 40개 테스트와 self-test 통과.

## 사용자 제공 DLP/BBP 인게임 설명

DLP는 태그 2개와 설명 4개, BBP는 태그 2개와 설명 3개를 독립 등록했습니다.
source_type=user_ingame_capture, verification=user_ingame_verified이며 사용자 제공 텍스트 전사입니다.
태그 자체로부터 추가 효과를 생성하지 않습니다. DLP의 '자유' 효과를 해석하지 않습니다.
BBP의 전반적 활동 성격은 role_description, DLP의 수비 능숙성 요구는 player_requirement로
구분합니다. 후자는 실제 수비 성과나 후방 잔류 보장이 아닙니다.
DLP의 '더 모험적으로 플레이하라'는 player_instructions에 별도 보존합니다.
명시된 설명만 expected_structure에 연결하고 observed_structure를 생성하지 않습니다.
BBP+AM 충돌이나 DLP의 항상 후방 잔류 규칙은 없습니다.
기존 CFD/WFD/IF/AM 및 나머지 역할 항목은 변경 전 데이터와 동일함을 확인했습니다.
검증: 전체 43개 테스트 및 기존 self-test 통과.

## 역할 카탈로그의 포메이션 활성화 조건

`role_catalog.json`과 `role_constraints.py`는 역할 행동과 분리된 UI 활성화 조건 계층입니다.
카탈로그의 `internal_id`가 식별자이며 `display_abbr`는 식별자로 사용하지 않습니다.
이 ID는 앱 내부 식별자일 뿐 FMF 내부 ID나 숨은 게임 ID가 아닙니다.

카탈로그는 `phase`, `internal_id`, `available_starting_positions`, 역할명,
display_abbr와 검증 상태, `formation_constraints`, `evidence`,
`role_behaviour_ref`를 보관합니다. 기존 역할 행동은 복사하지 않고
`role_behaviours.json`을 참조합니다. `resolve_catalog()`이 호출될 때만
`role_tags`, `described_behaviours`, `player_instructions`, 병합된 evidence를
읽기 전용 역할 보기로 만듭니다. 위치가 실제로 확인되지 않은 역할은 빈 목록과
`unknown`으로 남습니다.

IP ACB/WCB/OCB와 OOP 와이드 센터백·스토핑 와이드 센터백·커버링 와이드 센터백은
각각 별도 ID와 `centre_back_line == 3` 제약을 갖습니다. OOP 중앙 수비수·스토핑 센터백·
커버링 센터백에는 이 제약이 없습니다. 제약은 UI 선택 가능 여부만 보고하며 역할 행동,
예상 구조, 경기 관측을 변경하지 않습니다.

`role_availability(role, centre_back_line_player_count)`는 2CB/4백에서 OOP 와이드 센터백
계열을 `inactive`, 3CB에서 `active`로 반환합니다. 인원수를 제공하지 않으면 `unknown`입니다.
검증: 전체 47개 테스트 및 기존 self-test 통과.

## Connectivity 골격

`connectivity_engine.py`는 `role_catalog.json`을 통해 역할을 해석하고,
`role_behaviours.json`의 검증된 described_behaviours만 사용해 IP 방향 edge 후보를 만듭니다.
노드는 configured_position과 resolved role을 분리하며, 해석하지 못한 역할은 unresolved로 남습니다.

초기 edge 유형은 defence_to_midfield, midfield_to_attacking_midfield,
attacking_midfield_to_forward, centre_to_wide, wide_to_centre뿐입니다.
출력 상태는 connected, weakly_connected, unsupported, unknown이며 숫자 점수는 없습니다.
source_basis와 target_basis는 각각 보내기·받기 근거를 따로 보존합니다.
OOP 역할은 IP Connectivity 그래프에 섞지 않습니다.

progression_chains는 defence → midfield → attacking_midfield → forward 구간에서
broken_progression_chain, weak_progression_chain, unknown_chain을 보고할 수 있습니다.
edge는 실제·예측 패스, 빈도, 거리, 성공률, 위치를 뜻하지 않습니다. 역할 시너지나 충돌 규칙도 없습니다.
검증: 전체 52개 테스트 및 기존 self-test 통과.

## 웹 API 준비용 순수 분석 파이프라인

`core/tactic_normalization.py`와 `core/pipeline.py`는 파일 경로, SQLite 연결, CLI 인자,
print 없이 tactic data와 주입받은 역할 데이터만 받아 JSON 호환 보고서를 반환합니다.
`analyze-tactic`의 기존 파일·DB 읽기는 adapter 역할을 유지하며, 읽은 데이터를 이 파이프라인에 전달합니다.
Connectivity edge에는 from_node, to_node, phase, connection_type, basis, evidence_ids,
limitations 필드도 병렬로 제공해 향후 전술판 연결선에 사용할 수 있습니다.

행동 근거 부재는 unknown입니다. structurally_unsupported은 행동 데이터에 명시적인
구조 차단 근거가 있을 때만 생성할 수 있으나, 현재 수집된 FM26 역할 데이터에는 해당 근거가 없습니다.
`data/role_family_coverage.json`은 10개 역할군의 IP/OOP 스키마 수용 상태와 현재 확인된
구체 역할 수만 기록하며, 미확인 역할명이나 행동을 만들지 않습니다.
# FM26 Tactical Lab Web MVP

웹 MVP는 Python 표준 라이브러리만 사용하며 `core.pipeline.analyze_tactic_data`의 얇은 소비자입니다. 웹 레이어에는 Connectivity 규칙이 없습니다.

```powershell
python -m web.app
```

주소: `http://127.0.0.1:8000`

현재 지원:

- IP tactic builder와 7개 configured-position preset
- catalog 및 `role_constraints` 기반 역할 availability
- Connectivity 시각화와 edge provenance
- 현재 전술의 read-only evidence sufficiency

현재 미지원:

- OOP analysis
- tactic score 및 자동 역할 추천
- login, cloud save

현재 evidence가 부족한 경우 `Unknown`은 정상 결과일 수 있으며, 전술의 좋고 나쁨을 뜻하지 않습니다. preset은 역할 행동이나 Connectivity를 추론하지 않습니다.

API: `GET /api/health`, `GET /api/presets`, `GET /api/roles`, `GET /api/sample`, `POST /api/analyze`, `POST /api/evidence-sufficiency`.

## Deployment readiness

### Local development

```powershell
python -m web.app
```

Local URL: `http://127.0.0.1:8000`

`HOST`와 `PORT` 환경 변수로 local server bind 주소와 포트를 정할 수 있습니다. 기본값은 각각 `127.0.0.1`, `8000`입니다. 플랫폼이 `PORT`를 제공하는 경우 해당 값을 읽습니다.

### Production adapter

`web.app:wsgi_application`은 provider-neutral WSGI entry point입니다. 실제 공개 배포에서는 호스팅 환경이 선택한 WSGI server를 이 adapter에 연결합니다. 현재 local MVP 명령은 계속 표준 라이브러리 `ThreadingHTTPServer`를 사용합니다.

Runtime에 필요한 것은 Python 표준 라이브러리, `core/`, `web/`, 루트의 역할·분석 모듈, 그리고 역할·전술 JSON data입니다. 외부 Python dependency는 없습니다. 테스트 파일, `__pycache__`, local SQLite DB, 임시 파일은 runtime package에서 제외할 수 있습니다. `data/fm26lab.db`는 local CLI 저장소이므로 Web MVP runtime의 필수 데이터가 아닙니다.

### Known limitations

- IP analysis only
- OOP evidence in progress
- no tactic scoring
- no recommendation engine
- no user accounts or cloud save

공개 배포 전에도 공식 evidence package는 staging 상태로 유지하며, 검토·import 절차와 배포 절차를 분리합니다.

## GitHub + Render deployment

### Repository requirements

Repository root에 `requirements.txt`, `.python-version`, `render.yaml`, `web/`, `core/`, 역할·분석 모듈과 required JSON data를 함께 올립니다. `.gitignore`는 local SQLite DB, virtual environment, bytecode, `.env`를 제외합니다. GitHub push와 Render 배포는 이 저장소에서 수행하지 않습니다.

### Python version

Local verification 기준은 Python `3.14.7`입니다. `.python-version`은 Render native runtime에서 현재 지원되는 Python `3.14.3`을 지정합니다. 이 프로젝트는 표준 라이브러리와 Gunicorn만 사용하므로 3.14 계열 호환성을 유지하지만, 실제 첫 Render build log에서 제공 런타임 버전을 확인합니다.

### Render Web Service

Dashboard 수동 설정 또는 repository root의 `render.yaml` Blueprint 중 하나를 사용할 수 있습니다. Blueprint는 provider 설정을 최소화하며 web service, Python runtime, build/start command, health check만 선언합니다.

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --bind 0.0.0.0:$PORT web.app:wsgi_application`
- Health check: `/api/health`

Local mode는 `HOST=127.0.0.1`, `PORT=8000` 기본값을 사용합니다. Render production mode에서 Gunicorn은 platform `PORT`에 `0.0.0.0`으로 bind합니다.

### Stateless/persistence notes

공개 Web의 preset, role selector, analyze, evidence sufficiency 요청은 SQLite write를 수행하지 않습니다. role JSON과 sample tactic은 read-only입니다. `data/fm26lab.db`는 local CLI 기능을 위한 저장소이며 Web request runtime에는 필요하지 않습니다.

### Free-tier limitations

Render Free web service는 15분 동안 inbound traffic이 없으면 중지되고, 다음 요청에서 약 1분의 cold start가 발생할 수 있습니다. Free service의 local filesystem 변경은 restart, redeploy, spin-down 시 유지되지 않습니다. 현재 Web MVP는 stateless이므로 local SQLite persistence에 의존하지 않습니다.
