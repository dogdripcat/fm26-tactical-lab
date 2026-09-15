// Configured-position formation recognition. Presentation coordinates and role data are never read.
const LINE_KEYS=['defence','wing_back','holding_midfield','midfield','attacking_midfield','forward'];
const bandToLine={defensive_line:'defence',wing_back_line:'wing_back',defensive_midfield:'holding_midfield',midfield:'midfield',attacking_midfield:'attacking_midfield',forward:'forward'};

function unknown(reason,profile={}){return {formation:'사용자 구성',status:'custom',reason,profile};}
function laneCount(rows){return rows.reduce((out,row)=>{out[row.lateral_slot]=(out[row.lateral_slot]||0)+1;return out;},{left:0,centre:0,right:0,unknown:0});}
function has(rows,lane){return rows.some(row=>row.lateral_slot===lane);}
function laneShape(rows,shape){
  const count=laneCount(rows);
  if(count.unknown)return false;
  if(shape==='centre')return rows.length===1&&count.centre===1;
  if(shape==='left_right')return rows.length===2&&count.left===1&&count.right===1;
  if(shape==='left_centre')return rows.length===2&&count.left===1&&count.centre===1;
  if(shape==='left_centre_right')return rows.length===3&&count.left===1&&count.centre===1&&count.right===1;
  if(shape==='wide_central_wide')return rows.length>=4&&count.left>=1&&count.right>=1&&(count.centre>=(rows.length===4?2:1)||rows.filter(row=>row.position_family==='midfield').length>=2);
  if(shape==='two_forwards')return rows.length===2&&(!count.unknown)&&((count.left&&count.right)||(count.centre===2)||(count.left&&count.centre)||(count.right&&count.centre));
  if(shape==='back_three')return rows.length===3&&rows.filter(row=>row.position_family==='centre_back').length===3&&has(rows,'left')&&has(rows,'centre')&&has(rows,'right');
  if(shape==='back_four')return rows.length===4&&rows.filter(row=>row.position_family==='centre_back').length>=2&&has(rows,'left')&&has(rows,'right');
  if(shape==='back_five')return rows.length===5&&rows.filter(row=>row.position_family==='centre_back').length>=3&&has(rows,'left')&&has(rows,'right');
  return false;
}

export function deriveFormationProfile(configuredPositions,registry){
  const byId=new Map((registry?.positions||[]).map(row=>[row.position_id,row]));
  const rows=(configuredPositions||[]).map(position=>byId.get(position)).filter(Boolean);
  if(rows.length!==(configuredPositions||[]).length)return {valid:false,reason:'unknown_configured_position'};
  const goalkeeper=rows.filter(row=>row.vertical_band==='goalkeeper');
  if(goalkeeper.length!==1)return {valid:false,reason:'goalkeeper_count'};
  const outfield=rows.filter(row=>row.vertical_band!=='goalkeeper');
  if(outfield.length!==10)return {valid:false,reason:'outfield_player_count'};
  const lines=Object.fromEntries(LINE_KEYS.map(key=>[key,[]]));
  for(const row of outfield){const key=bandToLine[row.vertical_band];if(!key)return {valid:false,reason:'unsupported_vertical_band'};lines[key].push(row);}
  const signature=Object.fromEntries(LINE_KEYS.map(key=>[key,lines[key].length]));
  return {valid:true,rows,outfield,lines,signature,lane_distribution:Object.fromEntries(LINE_KEYS.map(key=>[key,laneCount(lines[key])]))};
}

function variantMatches(profile,variant){
  if(!LINE_KEYS.every(key=>profile.signature[key]===(variant.signature?.[key]||0)))return false;
  return Object.entries(variant.lanes||{}).every(([line,shape])=>laneShape(profile.lines[line]||[],shape));
}

export function recognizeFormation(configuredPositions,registry,formationFamilies){
  const profile=deriveFormationProfile(configuredPositions,registry);
  if(!profile.valid)return unknown(profile.reason,profile);
  const matches=[];
  for(const family of formationFamilies?.families||[])for(const variant of family.variants||[])if(variantMatches(profile,variant))matches.push(family);
  const distinct=[...new Map(matches.map(family=>[family.id,family])).values()];
  if(distinct.length!==1)return unknown(distinct.length?'ambiguous_structural_match':'no_supported_structural_match',profile);
  return {formation:distinct[0].display,status:'recognized',family_id:distinct[0].id,profile};
}
