export function normalizeTacticData(tactic, aliases, teamInstructionCatalog) {
  const normalized = structuredClone(tactic || {}), changes = [];
  for (const [phase, key] of [['IP', 'ip_roles'], ['OOP', 'oop_roles']]) {
    for (const [position, value] of Object.entries(normalized[key] || {})) {
      const replacement = typeof value === 'string' ? (aliases[phase]?.[value] || value) : value;
      if (replacement !== value) { normalized[key][position] = replacement; changes.push({phase, position, before:value, after:replacement}); }
    }
  }
  for (const [phase, key] of [['IP','ip_team_instructions'], ['OOP','oop_team_instructions']]) {
    if (key in normalized) normalized[key] = normalizeTeamInstructions(normalized[key], phase, teamInstructionCatalog);
  }
  return {normalized, changes};
}
export function normalizeTeamInstructions(raw, phase, catalog) {
  if (raw == null) return {};
  if (typeof raw !== 'object' || Array.isArray(raw)) throw new Error(`${phase.toLowerCase()}_team_instructions must be an object`);
  const byId = new Map((catalog.instructions || []).map(row => [row.internal_id,row]));
  const out = {};
  for (const [categoryId,valueId] of Object.entries(raw)) {
    const category=byId.get(categoryId);
    if (!category || category.phase !== phase) throw new Error(`Unknown or cross-phase team instruction: ${categoryId}`);
    const value=(category.selectable_values||[]).find(row=>row.internal_id===valueId);
    if (!value || value.verification !== 'user_ingame_verified') throw new Error(`Unverified team instruction value: ${valueId}`);
    out[categoryId]=valueId;
  }
  return out;
}
