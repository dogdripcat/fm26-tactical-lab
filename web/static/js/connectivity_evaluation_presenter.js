// Presentation-only formatter.  All tactical states come from connectivity_evaluation.
const labels={left:'왼쪽',centre:'중앙',right:'오른쪽'};
const positionLabel=nodeId=>nodeId.split(':').at(-1);
const regionNames=regions=>regions.map(region=>labels[region]).join('과 ');
const regionPrimary={multiple_structurally_distinct_route_families:'복수 경로 있음',complete_route_present:'전방 연결 있음',no_complete_regional_route_detected:'완결 경로 미확인'};

function continuityText(line){
  if(line.status==='continuous')return '점유한 각 라인 사이에 전진 연결이 이어집니다.';
  if(line.status==='partial')return '일부 라인 사이의 전진 연결이 제한적입니다.';
  return '전방으로 이어지는 과정에서 구조적으로 끊기는 구간이 있습니다.';
}
function dependencyText(item){
  const position=positionLabel(item.node_id),regions=regionNames(item.affected_regions||[]);
  if(item.impact==='all_complete_progression_removed')return `${position} 위치가 제외되면 현재 구조에서 완결된 전진 경로가 남지 않습니다.`;
  if(item.impact==='regional_progression_removed')return `${position} 위치가 제외되면 ${regions}의 전방 연결이 구조적으로 끊깁니다.`;
  return `${position} 위치가 제외되면 하나의 구조적 대안 경로가 사라집니다.`;
}
function supportText(support){
  if((support.nodes||[]).some(item=>item.status==='fallback_not_detected'))return '전진 경로는 존재하지만 일부 연결점에서 되돌려 순환할 선택지가 제한적입니다.';
  return '전진 참여 위치에서 같은 라인이나 후방으로 공을 다시 연결할 구조적 선택지가 있습니다.';
}

export function presentConnectivityEvaluation(evaluation,v2){
  const regional=evaluation.regional_connectivity||{},available=['left','centre','right'].filter(region=>regional[region]?.status!=='no_complete_regional_route_detected');
  const summary=evaluation.line_continuity?.status==='continuous'&&available.length?`수비선에서 전방까지 이어지는 구조적 연결이 존재하며, ${regionNames(available)}을 통해 전진 경로를 사용할 수 있습니다.`:evaluation.line_continuity?.status==='partial'?'일부 점유 라인 사이의 연결이 제한되어 전방까지 이어지는 구조를 확인해야 합니다.':'전방까지 이어지는 완결 경로가 현재 확인되지 않습니다.';
  const routeFamilies=evaluation.route_diversity?.families||[];
  const regions=['left','centre','right'].map(region=>{
    const value=regional[region]||{status:'no_complete_regional_route_detected'},outgoing=region==='left'?'left_to_centre':region==='right'?'right_to_centre':null,incoming=region==='left'?'centre_to_left':region==='right'?'centre_to_right':null,access=outgoing&&evaluation.cross_region_access?.[outgoing]?.status==='access_detected'||incoming&&evaluation.cross_region_access?.[incoming]?.status==='access_detected'||region==='centre'&&['left_to_centre','right_to_centre','centre_to_left','centre_to_right'].some(key=>evaluation.cross_region_access?.[key]?.status==='access_detected');
    const representatives=routeFamilies.filter(family=>family.dominant_region===region).map(family=>family.representative_route_id);
    return {region,title:labels[region],primary:regionPrimary[value.status]||'완결 경로 미확인',detail:value.status==='multiple_structurally_distinct_route_families'?'구조적으로 다른 전진 경로가 있습니다.':value.status==='complete_route_present'?'전방까지 이어지는 경로가 있습니다.':'현재 완결된 전진 경로가 확인되지 않습니다.',access:access?(region==='centre'?'좌·우 연결 가능':'중앙 연결 가능'):'',representative_route_ids:representatives};
  });
  const dependency=(evaluation.connector_dependency||[]).filter(item=>['regional_progression_removed','all_complete_progression_removed'].includes(item.impact)).map(item=>({...item,text:dependencyText(item)}));
  const dependencyNodes=new Set((evaluation.connector_dependency||[]).filter(item=>item.impact!=='no_meaningful_impact').map(item=>item.node_id));
  const shared=(v2.bottlenecks||[]).filter(item=>!dependencyNodes.has(item.node_id)).map(item=>({node_id:item.node_id,text:`${positionLabel(item.node_id)} 위치는 여러 전진 경로가 이 연결점을 공유합니다.`}));
  const roleAdjustments=(evaluation.role_adjustments||[]).map(item=>({...item,text:`${positionLabel(item.node_id)} 위치: ${item.interpretation}` }));
  return {summary,continuity:continuityText(evaluation.line_continuity||{}),regions,progression:available.length?`${regionNames(available)}을 통한 완결 전진 경로가 확인됩니다.`:'완결된 전진 경로가 확인되지 않습니다.',dependency,shared,support:supportText(evaluation.support_recycle||{}),deadEnds:(evaluation.dead_ends||[]).map(item=>`${positionLabel(item.node_id)} 위치에서는 전진 이후 이어갈 구조적 선택지가 제한됩니다.`),isolated:(evaluation.isolated_nodes||[]).map(item=>`${positionLabel(item.node_id)} 위치는 현재 구조에서 주변 연결 선택지가 제한되어 있습니다.`),roleAdjustments,limitations:['이 평가는 포메이션과 역할의 구조적 연결 가능성을 분석합니다. 실제 패스 성공률, 선수 능력치, 상대 압박, 경기 상황은 반영하지 않습니다.',...(evaluation.limitations||[])],hasCompleteProgression:Boolean(available.length)};
}
