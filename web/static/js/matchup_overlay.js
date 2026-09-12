// Formation-only presentation data for the opponent comparison screen.
// It deliberately has no player, role, instruction, or match-event inference.
export const OPPONENT_SHAPES={
  '4-3-3':[[50,89],[22,74],[42,74],[58,74],[78,74],[30,51],[50,51],[70,51],[20,22],[50,15],[80,22]],
  '4-2-3-1':[[50,89],[22,74],[42,74],[58,74],[78,74],[38,56],[62,56],[20,35],[50,33],[80,35],[50,14]],
  '4-4-2':[[50,89],[22,74],[42,74],[58,74],[78,74],[20,51],[42,51],[58,51],[80,51],[42,15],[58,15]],
  '4-1-4-1':[[50,89],[22,74],[42,74],[58,74],[78,74],[50,61],[20,42],[42,42],[58,42],[80,42],[50,14]],
  '3-4-2-1':[[50,89],[28,74],[50,74],[72,74],[20,53],[42,53],[58,53],[80,53],[38,31],[62,31],[50,14]],
  '3-5-2':[[50,89],[28,74],[50,74],[72,74],[18,52],[38,52],[50,47],[62,52],[82,52],[42,15],[58,15]],
  '3-4-3':[[50,89],[28,74],[50,74],[72,74],[20,52],[42,52],[58,52],[80,52],[20,20],[50,14],[80,20]]
};

const configured={
  left:new Set(['LB','LCB','wing_back_left','DML','MCL','ML','AML']),
  right:new Set(['RB','RCB','wing_back_right','DMR','MCR','MR','AMR']),
  back:new Set(['GK','LB','LCB','CB','DC','RCB','RB','wing_back_left','wing_back_right']),
  middle:new Set(['DML','DM','DMR','MCL','MC','MCR','ML','MR']),
  attack:new Set(['AML','AMC','AMR','ST','CF'])
};
const blank=()=>({left:{back:0,middle:0,attack:0},centre:{back:0,middle:0,attack:0},right:{back:0,middle:0,attack:0}});
const laneFor=value=>value<35?'left':value>65?'right':'centre';
const bandFor=value=>value<36?'attack':value<66?'middle':'back';
const ownLane=position=>configured.left.has(position)?'left':configured.right.has(position)?'right':'centre';
const ownBand=position=>configured.back.has(position)?'back':configured.middle.has(position)?'middle':'attack';
const total=(profile,lane)=>Object.values(profile[lane]).reduce((sum,value)=>sum+value,0);

export function opponentProfile(shape){const profile=blank();(shape||[]).forEach(([x,y])=>profile[laneFor(x)][bandFor(y)]++);return profile;}
export function ownProfile(positions){const profile=blank();(positions||[]).forEach(position=>profile[ownLane(position)][ownBand(position)]++);return profile;}

function observation(state,region,band,text,detail){return {state,region,band,text,detail};}
export function buildMatchupObservations(ownPositions, opponentShape){const own=ownProfile(ownPositions),opponent=opponentProfile(opponentShape),items=[];
  if(opponent.centre.middle>own.centre.middle)items.push(observation('주의','centre','middle','중앙 중원에서 상대가 더 밀집할 수 있습니다.','구성된 중앙 중원 위치 수에서 상대가 더 많습니다.'));
  else if(own.centre.middle>opponent.centre.middle)items.push(observation('활용 가능','centre','middle','중앙 중원에서 연결 공간을 활용할 여지가 있습니다.','구성된 중앙 중원 위치 수에서 우리 쪽이 더 많습니다.'));
  else if(own.centre.middle&&opponent.centre.middle)items.push(observation('충돌 집중','centre','middle','중앙 중원에서 구조적 충돌이 집중됩니다.','양쪽이 중앙 중원에 같은 수의 구성 위치를 두고 있습니다.'));
  if(opponent.centre.attack>own.centre.back)items.push(observation('주의','centre','back','중앙 후방에서 상대 전방 점유를 주의하세요.','상대 중앙 공격 위치 수가 우리 중앙 후방 위치 수보다 많습니다.'));
  else if(own.centre.attack>opponent.centre.back)items.push(observation('활용 가능','centre','attack','상대 중앙 후방에 전진 공간을 활용할 여지가 있습니다.','우리 중앙 공격 위치 수가 상대 중앙 후방 위치 수보다 많습니다.'));
  else if(own.centre.attack&&opponent.centre.back)items.push(observation('충돌 집중','centre','attack','중앙 최전방과 후방의 구조적 충돌이 예상됩니다.','우리 중앙 공격과 상대 중앙 후방의 구성 위치 수가 같습니다.'));
  for(const [region,label] of [['left','왼쪽'],['right','오른쪽']]){const ours=total(own,region),theirs=total(opponent,region);if(theirs>ours)items.push(observation('주의',region,'middle',`${label} 측면에서 상대 점유가 더 많을 수 있습니다.`,`구성된 ${label} 측면 위치 수에서 상대가 더 많습니다.`));else if(ours>theirs)items.push(observation('활용 가능',region,'middle',`${label} 측면에서 공간을 활용할 여지가 있습니다.`,`구성된 ${label} 측면 위치 수에서 우리 쪽이 더 많습니다.`));else if(ours&&theirs)items.push(observation('충돌 집중',region,'middle',`${label} 측면에서 구조적 충돌이 집중됩니다.`,`양쪽이 ${label} 측면에 같은 수의 구성 위치를 두고 있습니다.`));}
  const order={'주의':0,'활용 가능':1,'충돌 집중':2};return items.sort((a,b)=>order[a.state]-order[b.state]||a.region.localeCompare(b.region)).slice(0,5);
}

export const zoneStyle={left:{left:'0%',width:'33.333%'},centre:{left:'33.333%',width:'33.334%'},right:{left:'66.667%',width:'33.333%'},back:{top:'66%',height:'34%'},middle:{top:'36%',height:'30%'},attack:{top:'0%',height:'36%'}};
