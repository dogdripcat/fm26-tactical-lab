const DATA_VERSION='fm26-tactical-lab-v1-2-0';
const dataUrl = name => {const url=new URL(`../data/${name}`, import.meta.url);url.searchParams.set('v',DATA_VERSION);return url;};
export async function loadJson(name) {
  const response = await fetch(dataUrl(name));
  if (!response.ok) throw new Error(`Static data could not load: ${name}`);
  return response.json();
}
export async function loadStaticData() {
  const [catalog, behaviours, registry, vocabulary, ers, teamInstructions, presets, aliases, attributeProfiles, tacticalStyles, tacticDefaults, playingApproaches, formationFamilies] = await Promise.all([
    loadJson('role_catalog.json'), loadJson('role_behaviours.json'), loadJson('configured_position_registry.json'),
    loadJson('connectivity_semantic_vocabulary.json'), loadJson('expected_role_space_ontology.json'),
    loadJson('team_instruction_catalog.json'), loadJson('presets.json'), loadJson('role_aliases.json'), loadJson('role_attribute_profiles.json'), loadJson('tactical_style_catalog.json'), loadJson('tactic_default_profiles.json'), loadJson('playing_approach_catalog.json'), loadJson('formation_families.json')
  ]);
  return {catalog, behaviours, registry, vocabulary, ers, teamInstructions, presets: presets.presets, aliases, attributeProfiles, tacticalStyles, tacticDefaults, playingApproaches, formationFamilies};
}
