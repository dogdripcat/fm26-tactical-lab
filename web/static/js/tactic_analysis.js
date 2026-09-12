import {normalizeTacticData} from './tactic_normalization.js';
import {buildConnectivity} from './connectivity_engine.js';
import {buildConnectivityV2} from './connectivity_engine_v2.js';
import {evaluateConnectivityV2} from './connectivity_qualitative_evaluator.js';
import {evaluateProgression} from './progression_evaluator.js';
import {evaluateSupport} from './support_evaluator.js';
import {present} from './analysis_presenter.js';
import {inputStatus} from './team_instructions.js';
export function analyzeTactic(tactic,data){const {normalized,changes}=normalizeTacticData(tactic,data.aliases,data.teamInstructions);const connectivity=buildConnectivity(normalized,data),connectivity_v2=buildConnectivityV2(normalized,data),connectivity_evaluation=evaluateConnectivityV2(connectivity_v2),progression_evaluation=evaluateProgression(connectivity_v2,connectivity_evaluation),support_evaluation=evaluateSupport(connectivity_v2,progression_evaluation);const result={connectivity,connectivity_v2,connectivity_evaluation,progression_evaluation,support_evaluation,normalization:{changes,input_mutated:false},team_instruction_input_status:inputStatus(normalized)};result.tactic_input={in_possession:{formation:tactic.ip_formation,positions:Object.keys(tactic.ip_roles||{}),roles:structuredClone(tactic.ip_roles||{}),team_instructions:structuredClone(tactic.ip_team_instructions||{})},out_of_possession:{formation:tactic.oop_formation,positions:Object.keys(tactic.oop_roles||{}),roles:structuredClone(tactic.oop_roles||{}),team_instructions:structuredClone(tactic.oop_team_instructions||{}),editing_status:'configured_not_evaluated',limitation:'OOP roles are retained as tactic input and are not consumed by the current evaluators.'}};result.presentation=present(result);return result;}
