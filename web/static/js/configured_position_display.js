const DISPLAY_LABELS = Object.freeze({
  forward_left: 'ST',
  forward_centre: 'ST',
  forward_right: 'ST',
  attacking_midfield_left: 'AM',
  attacking_midfield_centre: 'AM',
  attacking_midfield_right: 'AM',
});

const PRESET_CENTRE_EQUIVALENTS = Object.freeze({
  forward_centre: 'ST',
  attacking_midfield_centre: 'AMC',
});

export function getConfiguredPositionDisplayLabel(positionId) {
  return DISPLAY_LABELS[positionId] || positionId;
}

export function normalizeConfiguredPositionForPreset(positionId) {
  return PRESET_CENTRE_EQUIVALENTS[positionId] || positionId;
}
