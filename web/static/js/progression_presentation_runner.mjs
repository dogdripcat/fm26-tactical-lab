import fs from 'node:fs';
import {presentProgressionEvaluation} from './progression_evaluation_presenter.js';
const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
process.stdout.write(JSON.stringify(presentProgressionEvaluation(input.progression_evaluation,input.connectivity_v2||{})));
