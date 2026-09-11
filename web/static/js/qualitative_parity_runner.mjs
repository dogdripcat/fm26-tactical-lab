import fs from 'node:fs';
import {analyzeTactic} from './tactic_analysis.js';
const root=new URL('../',import.meta.url);
const read=name=>JSON.parse(fs.readFileSync(new URL(name,root),'utf8'));
const tactic=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const data={catalog:read('data/role_catalog.json'),behaviours:read('data/role_behaviours.json'),registry:read('data/configured_position_registry.json'),teamInstructions:read('data/team_instruction_catalog.json'),aliases:read('data/role_aliases.json')};
const result=analyzeTactic(tactic,data);
process.stdout.write(JSON.stringify({connectivity_v2:result.connectivity_v2,connectivity_evaluation:result.connectivity_evaluation}));
