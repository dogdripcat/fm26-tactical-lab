import fs from 'node:fs';
import {analyzeTactic} from './tactic_analysis.js';
const root=new URL('../',import.meta.url);
const read=name=>JSON.parse(fs.readFileSync(new URL(name,root),'utf8'));
const tactic=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const data={catalog:read('data/role_catalog.json'),behaviours:read('data/role_behaviours.json'),registry:read('data/configured_position_registry.json'),teamInstructions:read('data/team_instruction_catalog.json'),aliases:read('data/role_aliases.json')};
const result=analyzeTactic(tactic,data), graph=result.connectivity;
const normalizeEdge=edge=>({from_node:edge.from_node,to_node:edge.to_node,path_type:edge.path_type,status:edge.status,source_method:edge.provenance.source_method,target_method:edge.provenance.target_method,semantic_ids:edge.provenance.semantic_ids,behaviour_ids:edge.provenance.behaviour_ids,evidence_ids:edge.provenance.evidence_ids,evidence_completeness:edge.provenance.evidence_completeness});
process.stdout.write(JSON.stringify({nodes:graph.nodes.map(n=>({node_id:n.node_id,role_internal_id:n.role_internal_id})),edges:graph.edges.map(normalizeEdge),progression_chains:graph.progression_chains.map(c=>({node_ids:c.node_ids,status:c.status})),isolated_nodes:graph.isolated_nodes.map(n=>n.node_id),evidence_completeness:graph.evidence_completeness,presentation:result.presentation}));
