// Presentation-only prioritisation. It consumes existing evaluator presenters
// and never creates routes, links, scores, or tactical claims.
const unique = items => [...new Map(items.filter(item => item?.title).map(item => [`${item.kind}:${item.title}:${(item.node_ids || []).join(',')}`, item])).values()];
const routeFor = item => item.representative_route_id || item.route_id || null;

function connectivityIssues(view) {
  return [
    ...(view.isolated || []).map(item => ({kind:'connectivity', priority:1, title:'연결 선택지 제한', reason:item, node_ids:[], link_ids:[]})),
    ...(view.deadEnds || []).map(item => ({kind:'connectivity', priority:1, title:'전진 뒤 연결 제한', reason:item, node_ids:[], link_ids:[]})),
    ...(view.dependency || []).map(item => ({kind:'connectivity', priority:2, title:'특정 위치 의존', reason:item.text, node_ids:[item.node_id].filter(Boolean), link_ids:[]})),
  ];
}
function progressionIssues(view) {
  return [
    ...(view.stalls || []).map(item => ({kind:'progression', priority:2, title:'전진 경로 정체', reason:item.text, node_ids:[item.node_id].filter(Boolean), link_ids:[], route_id:routeFor(item)})),
    ...(view.dependencies || []).map(item => ({kind:'progression', priority:2, title:'전진 경로 의존', reason:item.text, node_ids:[item.node_id].filter(Boolean), link_ids:[], route_id:routeFor(item)})),
    ...(view.cards || []).filter(card => card.primary === '직접 전진 없음').map(card => ({kind:'progression', priority:2, title:`${card.title} 전진 경로 제한`, reason:card.detail, node_ids:[], link_ids:[], route_id:routeFor(card)})),
  ];
}
function supportIssues(view) {
  return [
    ...(view.isolated || []).map(item => ({kind:'support', priority:1, title:'수신 뒤 지원 단절', reason:item.text, node_ids:item.node_ids || [], link_ids:item.link_ids || []})),
    ...(view.single || []).map(item => ({kind:'support', priority:3, title:'후속 선택지 부족', reason:item.text, node_ids:item.node_ids || [], link_ids:item.link_ids || []})),
    ...(view.dependencies || []).map(item => ({kind:'support', priority:3, title:'특정 위치 의존', reason:item.text, node_ids:item.node_ids || [], link_ids:item.link_ids || []})),
  ];
}
function strengths(connectivity, progression, support) {
  const found = [
    ...(progression.cards || []).filter(card => card.primary === '전방까지 전진').map(card => ({kind:'progression', title:`${card.title} 전진 경로 확보`, reason:card.detail, node_ids:[], link_ids:[], route_id:routeFor(card)})),
    ...(support.cards || []).filter(card => !card.primary.includes('미확인') && !card.detail.includes('없는 위치') && !card.detail.includes('집중')).map(card => ({kind:'support', title:`${card.title} 후속 지원 구조`, reason:card.detail, node_ids:card.node_ids || [], link_ids:card.link_ids || []})),
    ...(connectivity.regions || []).filter(region => region.primary === '복수 경로 있음' || region.primary === '전방 연결 있음').map(region => ({kind:'connectivity', title:`${region.title} 연결 연속성`, reason:region.detail, node_ids:[], link_ids:[], route_id:(region.representative_route_ids || [])[0] || null})),
  ];
  return unique(found).slice(0,2);
}

export function presentAnalysisResults({connectivity, progression, support}) {
  const cards = [
    {kind:'connectivity', title:'연결성', headline:connectivity.continuity, explanation:connectivity.summary, regions:(connectivity.regions || []).filter(row => row.primary !== '완결 경로 미확인').map(row => row.title)},
    {kind:'progression', title:'전진성', headline:progression.continuity, explanation:progression.summary, regions:(progression.cards || []).filter(row => row.primary !== '직접 전진 없음').map(row => row.title)},
    {kind:'support', title:'지원 구조', headline:support.summary, explanation:'공을 받은 뒤 이어갈 구조적 선택지를 현재 연결선 기준으로 표시합니다.', regions:(support.cards || []).filter(row => !row.primary.includes('미확인')).map(row => row.title)},
  ];
  const issues = unique([...connectivityIssues(connectivity), ...progressionIssues(progression), ...supportIssues(support)]).sort((a,b) => a.priority - b.priority).slice(0,3);
  return {cards, issues, strengths:strengths(connectivity, progression, support)};
}
