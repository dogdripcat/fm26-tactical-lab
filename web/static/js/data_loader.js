const dataUrl = name => new URL(`../data/${name}`, import.meta.url);
export async function loadJson(name) {
  const response = await fetch(dataUrl(name));
  if (!response.ok) throw new Error(`Static data could not load: ${name}`);
  return response.json();
}
export async function loadStaticData() {
  const [catalog, behaviours, registry, vocabulary, ers, teamInstructions, presets, aliases] = await Promise.all([
    loadJson('role_catalog.json'), loadJson('role_behaviours.json'), loadJson('configured_position_registry.json'),
    loadJson('connectivity_semantic_vocabulary.json'), loadJson('expected_role_space_ontology.json'),
    loadJson('team_instruction_catalog.json'), loadJson('presets.json'), loadJson('role_aliases.json')
  ]);
  return {catalog, behaviours, registry, vocabulary, ers, teamInstructions, presets: presets.presets, aliases};
}
