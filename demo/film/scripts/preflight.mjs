// Export gate; run after manifest.mjs. Drafts report missing captures, finals refuse them.
import {readFileSync} from 'node:fs';
const root = new URL('..', import.meta.url).pathname;
const manifest = JSON.parse(readFileSync(root + 'src/generated/manifest.json'));
const status = JSON.parse(readFileSync(root + 'src/status.json'));
const beats = readFileSync(root + 'src/beats.ts', 'utf8');
const files = [...new Set([...beats.matchAll(/(?:screen|phone): '([^']+)'/g)].map(x => x[1]))];
const missing = files.filter(f => !manifest.footage[f]);
const issues = [];
if (missing.length) issues.push(`Missing ${missing.length}/${files.length} clips: ${missing.join(', ')}`);
if (status.draft) issues.push('Closing card is marked draft');
if (status.rows.some(r => r.status === 'pending')) issues.push('Closing evidence rows remain pending');
if (!['owner', 'elevenlabs'].includes(manifest.voSource)) issues.push(`Voice is ${manifest.voSource}`);
console.log(issues.length ? issues.join('\n') : 'Media and closing-status gates passed; owner playback/redaction review still required.');
if (process.argv.includes('--final') && issues.length) process.exitCode = 1;
