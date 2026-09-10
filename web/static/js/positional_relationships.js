const lateralOrder={left:0,centre:1,right:2};
export function registryIndex(registry){ return new Map((registry.positions||[]).map(row=>[row.position_id,row])); }
export function normalizeConfiguredPosition(raw,registry){
  if(typeof raw!=='string') return null;
  if((registry.canonical_position_ids||[]).includes(raw)) return raw;
  const alias=(registry.legacy_input_aliases||[]).find(row=>row.raw_position===raw);
  return alias?.status==='resolved'?alias.canonical_position_id:null;
}
export function buildPositionNode(phase, configuredPosition, roleInternalId, registry){
  const position=normalizeConfiguredPosition(configuredPosition,registry)||configuredPosition;
  const definition=registryIndex(registry).get(position);
  const base={node_id:`${phase}:${position}`,phase,configured_position:position,role_internal_id:roleInternalId||null,expected_role_space:{status:'unknown',items:[]}};
  return definition?{...base,position_family:definition.position_family,vertical_band:definition.vertical_band,vertical_index:definition.vertical_index,lateral_slot:definition.lateral_slot}:{...base,position_family:'unknown',vertical_band:'unknown',vertical_index:null,lateral_slot:'unknown'};
}
export function calculateConfiguredPositionRelation(source,target){
  const basis={source:pick(source),target:pick(target)};
  if(source.phase!==target.phase||!Number.isInteger(source.vertical_index)||!Number.isInteger(target.vertical_index)) return {status:'unknown',relations:[],basis};
  const relations=[], s=source.lateral_slot,t=target.lateral_slot, known=s in lateralOrder&&t in lateralOrder;
  if(known){const d=lateralOrder[t]-lateralOrder[s];if(d===0)relations.push('same_lateral_slot');else if(Math.abs(d)===1)relations.push('adjacent_lateral_slot');if(s==='centre'&&t!=='centre')relations.push('centre_to_wide');if(s!=='centre'&&t==='centre')relations.push('wide_to_centre');}
  const v=target.vertical_index-source.vertical_index;
  relations.push(v===0?'same_vertical_band':v===1?'one_band_forward':v>1?'multiple_bands_forward':v===-1?'one_band_backward':'multiple_bands_backward');
  if(known&&s!==t&&v!==0)relations.push(v>0?'forward_diagonal':'backward_diagonal');
  const order=['same_lateral_slot','adjacent_lateral_slot','centre_to_wide','wide_to_centre','same_vertical_band','one_band_forward','multiple_bands_forward','one_band_backward','multiple_bands_backward','forward_diagonal','backward_diagonal'];
  return {status:'known',relations:order.filter(x=>relations.includes(x)),basis};
}
function pick(node){return Object.fromEntries(['configured_position','position_family','vertical_band','vertical_index','lateral_slot'].map(k=>[k,node[k]]));}
