import fs from 'node:fs';
import {evaluateConnectivityV2} from './connectivity_qualitative_evaluator.js';
import {presentConnectivityEvaluation} from './connectivity_evaluation_presenter.js';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const v2=input.connectivity_v2||input;
const evaluation=input.connectivity_evaluation||evaluateConnectivityV2(v2);
process.stdout.write(JSON.stringify(presentConnectivityEvaluation(evaluation,v2)));
