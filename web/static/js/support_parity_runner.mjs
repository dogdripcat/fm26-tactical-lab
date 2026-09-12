import fs from 'node:fs';
import {analyzeTactic} from './tactic_analysis.js';
import {evaluateConnectivityV2} from './connectivity_qualitative_evaluator.js';
import {evaluateProgression} from './progression_evaluator.js';
import {evaluateSupport} from './support_evaluator.js';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
if(input.connectivity_v2){process.stdout.write(JSON.stringify(evaluateSupport(input.connectivity_v2,input.progression_evaluation||evaluateProgression(input.connectivity_v2,input.connectivity_evaluation||evaluateConnectivityV2(input.connectivity_v2)))));}else{const root=new URL('../',import.meta.url),read=name=>JSON.parse(fs.readFileSync(new URL(name,root),'utf8'));const data={catalog:read('data/role_catalog.json'),behaviours:read('data/role_behaviours.json'),registry:read('data/configured_position_registry.json'),teamInstructions:read('data/team_instruction_catalog.json'),aliases:read('data/role_aliases.json')};process.stdout.write(JSON.stringify(analyzeTactic(input,data).support_evaluation));}
