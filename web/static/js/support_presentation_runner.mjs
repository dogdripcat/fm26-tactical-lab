import fs from 'node:fs';
import {presentSupportEvaluation} from './support_evaluation_presenter.js';

const input=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
process.stdout.write(JSON.stringify(presentSupportEvaluation(input.support_evaluation||input)));
