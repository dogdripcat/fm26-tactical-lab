# Role Catalogue Integrity & Missing Role Recovery — Phase 2

## Scope and result

Before and after the production catalogue contains 69 identities: 37 IP and 32 OOP. No verified role identity was missing from the user-verified role-family matrix, so no role was added, merged, renamed, or moved between phases. This is a successful recovery result: absence of behaviour evidence is not treated as absence of role identity.

## Family coverage

| Starting-position family | IP catalog memberships | OOP catalog memberships | Matrix result |
|---|---:|---:|---|
| Forward | 2 | 0 | IP Centre Forward and Channel Forward present; no user-verified OOP Forward identity recorded. |
| Winger | 6 | 4 | Complete against supplied matrix; two IP Playmaking-Winger identities remain unresolved. |
| Attacking Midfield | 5 | 3 | Complete. |
| Central Midfield | 6 | 4 | Complete; shared IP identities are intentionally counted in both AM and CM. |
| Wide Midfield | 4 | 3 | Complete. |
| Defensive Midfield | 5 | 3 | Complete. |
| Wing-Back | 4 | 3 | Complete. |
| Full-Back | 5 | 3 | Complete. |
| Centre-Back | 6 | 6 | Complete; verified three-CB availability constraints remain separate from behaviour evidence. |
| Goalkeeper | 3 | 3 | Complete. |

The authoritative per-role matrix, including internal ID, starting-position availability, abbreviation verification, behaviour coverage, semantic readiness, and ERS status, remains available in `data/role_source_manifest.json` and the preserved tactical-input audit.

## Shared identity and identity status

IP AM, advanced playmaker, and channel midfielder are deliberately shared across AM/CM only where the user-verified starting-position data records both. IP Wing-Back, Inside Wing-Back, Playmaking Wing-Back, Inside Winger, Playmaking Winger, and Winger similarly retain their recorded shared availability without role duplication.

`catalog:ip:winger:pw-legacy-name` and `catalog:ip:winger:playmaking-winger` remain separate unresolved identities. They are excluded from the default selector and returned only as `unresolved_roles`; they are not silently treated as verified or merged.

## Forward / ST audit

The verified IP Forward selector contains exactly:

- `catalog:ip:fw:cfd` — 센터 포워드 (`CFD` verified)
- `catalog:ip:fw:chf` — 채널 포워드 (`CHF` verified)

`CHF` has no registered behaviour evidence but remains selectable because role identity and behaviour coverage are independent. No OOP Forward identity is present because the supplied user-verified family matrix contains none.

The following names are not production roles: Target Forward, Tracking Centre Forward, Poacher, and Wide Outlet Winger. They are recorded in `data/missing_role_candidates.json` with source provenance and required verification. No Korean display name, abbreviation, phase, or configured position has been invented.

## Selector policy

The selector filters by phase, configured starting position, verified availability constraint, and identity status. It does not filter by behaviour coverage, connectivity semantics, or ERS coverage. A verified identity with `identity_only` coverage therefore remains selectable and is displayed with its evidence-coverage label.

Unresolved identities are not mixed into the default selectable list. The Web UI retains search and selection UX, and now displays them in a separate `검증 보류 역할 identity` list.

## Evidence gap summary

The catalogue has 10 partial behaviour roles and the remaining verified identities are mostly `identity_only`; OOP behaviour evidence is especially sparse. This is an analysis-evidence gap, not a catalogue-identity gap. No behaviour, semantic, ERS, or compatibility data was created in this phase.

## Validation

- User-verified role-family matrix coverage and phase separation are tested.
- Verified identities with no behaviour/semantic/ERS evidence remain selectable.
- Unresolved identities are kept out of the default selector.
- The missing-role candidate registry cannot affect the production selector.
- Existing Full-Back/Wing-Back cross-availability remains catalog-driven.
