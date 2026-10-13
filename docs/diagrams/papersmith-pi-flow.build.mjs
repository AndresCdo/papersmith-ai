/**
 * The source of `papersmith-pi-flow.html` and its PNG beside this file.
 *
 * It is here, and not only in the throwaway `.archify/` folder it was authored
 * in, because a diagram whose source lives outside the repository cannot be
 * regenerated from a clone -- and a diagram nobody can regenerate stops being
 * evidence and becomes an assertion.
 *
 *   node docs/diagrams/papersmith-pi-flow.build.mjs /tmp/flow/candidate.json
 *   node <archify-3.0.1>/bin/archify.mjs finalize architecture \
 *     /tmp/flow/candidate.json /tmp/flow/papersmith-pi-flow.html \
 *     --repo-root . --quality showcase --json
 *
 * `agentMeta` reads the shipped agent definitions, and every node's `sources`
 * names the repository path and line range it was transcribed from, so the
 * drawing is checkable against the code rather than trusted.
 *
 * Every label is English. The rendered page used to be Spanish through a
 * vendored translation table (`locales/es.json`, Archify 3.0.1, MIT); the
 * artifact is English now, so the table is gone and the labels are literal.
 */
import fs from 'fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const REPO = fileURLToPath(new URL('../../', import.meta.url)).replace(/\/$/, '');

const S=(path,line,end_line)=>{const r={path};if(line)r.line=line;if(end_line)r.end_line=end_line;return [r];};

const agentMeta=n=>{const fm=fs.readFileSync(`${REPO}/.pi/agents/${n}.md`,'utf8').split('---')[1];
 const tools=[...fm.split('tools:')[1].matchAll(/^\s+-\s+(\S+)/gm)].map(m=>m[1]);
 const caps=[];if(tools.some(t=>t==='write'||t==='edit'))caps.push('writes');if(tools.includes('bash'))caps.push('bash');if(tools.includes('mcp'))caps.push('MCP');
 const st=(fm.match(/^stretch:\s*(\S+)/m)||[])[1];
 const endLine=fm.split('\n').length;
 return {sub:caps.length?'reads · '+caps.join(' · '):'read-only',tag:st?`stretch: ${st}`:undefined,end:endLine};};
const A=n=>S(`.pi/agents/${n}.md`,1,agentMeta(n).end);
const K=(n,l,e)=>[{path:`.pi/prompts/${n}.md`,line:1,end_line:7,label:'template /'+n},{path:`skills/${n}/SKILL.md`,line:l,end_line:e}];
const W=200;
const n=(id,lane,col,type,label,sublabel,extra={})=>({id,lane,col,type,label,sublabel,width:Math.max(120,Math.ceil(label.length*6.9+16),Math.ceil(sublabel.length*5.4+20)),...extra});
const nodes=[
 n('piMd','pi',0,'external','.pi/APPEND_SYSTEM.md','Pi system prompt',{sources:S('.pi/APPEND_SYSTEM.md',1,27)}),
 n('canon','pi',1,'database','skills/','canonical · .pi/skills link',{tag:'setup:harnesses',sources:[{path:'.pi/APPEND_SYSTEM.md',line:14,end_line:18},{path:'package.json',line:16}]}),
 n('sync','pi',2,'messagebus','sync-repo-harness.py','writes the .pi/ projection',{tag:'--check',sources:S('scripts/sync-repo-harness.py',44,52)}),
 n('piDir','pi',3,'database','.pi/','prompts · agents · extensions',{sources:S('.pi/APPEND_SYSTEM.md',20,32)}),
 n('subagents','pi',4,'external','pi-subagents','package that reads .pi/agents',{sources:S('.pi/APPEND_SYSTEM.md',29,33)}),
 n('plaus','plaus',0,'frontend','/plausibility','idea in ≥ 2 sentences',{tag:'.pi/prompts',sources:K('plausibility',19,21)}),
 n('scout','plaus',1,'backend','sota-scout',agentMeta('sota-scout').sub,{...(agentMeta('sota-scout').tag?{tag:agentMeta('sota-scout').tag}:{}),sources:A('sota-scout')}),
 n('grapher','plaus',2,'backend','sota-grapher',agentMeta('sota-grapher').sub,{...(agentMeta('sota-grapher').tag?{tag:agentMeta('sota-grapher').tag}:{}),sources:A('sota-grapher')}),
 n('screener','plaus',3,'backend','novelty-screener',agentMeta('novelty-screener').sub,{...(agentMeta('novelty-screener').tag?{tag:agentMeta('novelty-screener').tag}:{}),sources:A('novelty-screener')}),
 n('plausGate','plaus',4,'security','Human acceptance','report → accepted',{sources:S('skills/plausibility/SKILL.md',139,162)}),
 n('pool','plaus',5,'database','sota-pool/','candidates · atlas.html',{sources:S('README.md',73)}),

 n('ingest','ingest',0,'frontend','/paper-ingestion','PDF in guidance/',{tag:'.pi/prompts',sources:K('paper-ingestion',27,29)}),
 n('ingestAgent','ingest',1,'backend','paper-ingestion',agentMeta('paper-ingestion').sub,{...(agentMeta('paper-ingestion').tag?{tag:agentMeta('paper-ingestion').tag}:{}),sources:A('paper-ingestion')}),
 n('guidance','ingest',4,'database','guidance/','Markdown + figures',{sources:S('README.md',74)}),

 n('delib','delib',0,'frontend','/proposal-deliberation','bound → published',{tag:'.pi/prompts',sources:K('proposal-deliberation',32,35)}),
 n('delibCli','delib',1,'messagebus','cli.mjs --serve','replace · insert · delete',{tag:'CREATE_SUCCESSOR',sources:S('skills/proposal-deliberation/SKILL.md',251,287)}),
 n('delibGate','delib',2,'security','Human acceptance','preview → accept',{sources:S('skills/proposal-deliberation/SKILL.md',33,62)}),
 n('delibPub','delib',3,'backend','deliberation-publish',agentMeta('deliberation-publish').sub,{...(agentMeta('deliberation-publish').tag?{tag:agentMeta('deliberation-publish').tag}:{}),sources:A('deliberation-publish')}),
 n('proposals','delib',4,'database','proposals/','rNN.md · rNN.graph.html',{sources:[{path:'README.md',line:75},{path:'skills/proposal-deliberation/SKILL.md',line:71,end_line:129}]}),

 n('expDelib','expdelib',0,'frontend','/experimental-deliberation','requires data-paper/',{tag:'.pi/prompts',sources:K('experimental-deliberation',34,38)}),
 n('expVal','expdelib',1,'backend','experimental-validation',agentMeta('experimental-validation').sub,{...(agentMeta('experimental-validation').tag?{tag:agentMeta('experimental-validation').tag}:{}),sources:A('experimental-validation')}),
 n('expGate','expdelib',2,'security','Human acceptance','deliberated = operator',{sources:S('skills/experimental-deliberation/SKILL.md',35,65)}),
 n('expPub','expdelib',3,'backend','experimental-publish',agentMeta('experimental-publish').sub,{...(agentMeta('experimental-publish').tag?{tag:agentMeta('experimental-publish').tag}:{}),sources:A('experimental-publish')}),
 n('experiments','expdelib',4,'database','experiments/','experimental protocol',{sources:S('README.md',77)}),

 n('impl','impl',0,'frontend','/proposal-implementation','standing → full-scale',{tag:'.pi/prompts',sources:K('proposal-implementation',96,101)}),
 n('implBuild','impl',1,'backend','implementation-build',agentMeta('implementation-build').sub,{...(agentMeta('implementation-build').tag?{tag:agentMeta('implementation-build').tag}:{}),sources:A('implementation-build')}),
 n('implWalk','impl',2,'backend','implementation-walk',agentMeta('implementation-walk').sub,{...(agentMeta('implementation-walk').tag?{tag:agentMeta('implementation-walk').tag}:{}),sources:A('implementation-walk')}),
 n('implGate','impl',3,'security','Authorizes a launch','operator only',{sources:S('README.md',1570)}),
 n('repo','impl',4,'database','implementations/<repo>','its own git + .venv',{sources:S('README.md',76)}),

 n('expImpl','expimpl',0,'frontend','/experimental-implementation','binding → full-scale',{tag:'.pi/prompts',sources:K('experimental-implementation',116,120)}),
 n('expBuild','expimpl',1,'backend','experiments-build',agentMeta('experiments-build').sub,{...(agentMeta('experiments-build').tag?{tag:agentMeta('experiments-build').tag}:{}),sources:A('experiments-build')}),
 n('expWalk','expimpl',2,'backend','experiments-walk',agentMeta('experiments-walk').sub,{...(agentMeta('experiments-walk').tag?{tag:agentMeta('experiments-walk').tag}:{}),sources:A('experiments-walk')}),
 n('expImplGate','expimpl',3,'security','Authorizes a launch','whole campaign',{sources:S('skills/experimental-implementation/SKILL.md',116,120)}),

 n('kaggle','creds',0,'frontend','/kaggle-accounts','taken-in → decided',{tag:'.pi/prompts',sources:K('kaggle-accounts',28,30)}),
 n('accCli','creds',1,'security','accounts_cli.py','validate --interactive',{tag:'TTY only',sources:S('skills/kaggle-accounts/SKILL.md',218,244)}),
 n('store','creds',2,'database','store/','validated credentials',{sources:S('README.md',79)}),

 n('guard','remote',4,'security','refuse-offpath-push.js','extension: watches bash',{tag:'tool_call',sources:[{path:'.pi/extensions/refuse-offpath-push.js',line:1,end_line:30},{path:'.pi/APPEND_SYSTEM.md',line:35,end_line:41}]}),
 n('remote','remote',0,'frontend','/remote-execution','reachable → returned',{tag:'.pi/prompts',sources:K('remote-execution',40,44)}),
 n('readiness','remote',1,'security','readiness + gate','single-use token',{sources:S('skills/remote-execution/SKILL.md',42)}),
 n('remoteCli','remote',2,'messagebus','remote_cli.py','submit · poll · fetch',{tag:'9 subcommands',sources:S('skills/remote-execution/SKILL.md',1401,1416)}),
 n('inbox','remote',3,'database','kaggle-inbox/','ledger + results',{sources:S('README.md',80)}),

 n('pw','write',0,'frontend','/paper-writing','sections/*.md → paper/',{tag:'.pi/prompts',sources:K('paper-writing',1094,1105)}),
 n('insumos','write',1,'backend','insumos-observer',agentMeta('insumos-observer').sub,{...(agentMeta('insumos-observer').tag?{tag:agentMeta('insumos-observer').tag}:{}),sources:A('insumos-observer')}),
 n('redactor','write',2,'backend','redactor',agentMeta('redactor').sub,{...(agentMeta('redactor').tag?{tag:agentMeta('redactor').tag}:{}),sources:A('redactor')}),
 n('contract','write',3,'backend','contract-auditor',agentMeta('contract-auditor').sub,{...(agentMeta('contract-auditor').tag?{tag:agentMeta('contract-auditor').tag}:{}),sources:A('contract-auditor')}),
 n('style','write',4,'backend','style-sampler',agentMeta('style-sampler').sub,{...(agentMeta('style-sampler').tag?{tag:agentMeta('style-sampler').tag}:{}),sources:A('style-sampler')}),
 n('grounding','figs',4,'backend','section-grounding-auditor',agentMeta('section-grounding-auditor').sub,{...(agentMeta('section-grounding-auditor').tag?{tag:agentMeta('section-grounding-auditor').tag}:{}),sources:A('section-grounding-auditor')}),

 n('paperCli','figs',0,'messagebus','paper_cli.py','write judges what comes back',{tag:'28 verbs',sources:S('skills/paper-writing/SKILL.md',1094,1105)}),
 n('diagram','figs',1,'backend','diagram-author',agentMeta('diagram-author').sub,{...(agentMeta('diagram-author').tag?{tag:agentMeta('diagram-author').tag}:{}),sources:A('diagram-author')}),
 n('figAud','figs',2,'backend','figure-auditor',agentMeta('figure-auditor').sub,{...(agentMeta('figure-auditor').tag?{tag:agentMeta('figure-auditor').tag}:{}),sources:A('figure-auditor')}),
 n('figRev','figs',3,'frontend','/figure-review','probe · raster, no changes',{tag:'.pi/prompts',sources:K('figure-review',1,12)}),
 n('paper','out',4,'database','paper/','main.tex · refs.bib',{sources:S('README.md',81)}),

 n('audit','audit',0,'frontend','/skill-audit','subject: any skill',{tag:'.pi/prompts',sources:K('skill-audit',23,23)}),
 n('auditRep','audit',1,'backend','audit-report',agentMeta('audit-report').sub,{...(agentMeta('audit-report').tag?{tag:agentMeta('audit-report').tag}:{}),sources:A('audit-report')}),
 n('report','audit',2,'database','Audit report','never repairs',{sources:S('skills/skill-audit/SKILL.md',670,677)}),
];
const e=(from,to,label,extra={})=>({id:`${from}-${to}`,from,to,...(label?{label}:{}),...extra});
const main={variant:'emphasis',role:'main'};
const edges=[
 e('plaus','ingest','top-5 to ingest',main),
 e('ingest','delib','guidance/',main),
 e('delib','impl','revision rNN',main),
 e('impl','expDelib','proof of concept',main),
 e('expDelib','expImpl','protocol + repo',main),
 e('expImpl','kaggle','job ready',main),
 e('kaggle','remote','accounts proven',main),
 e('remote','pw','measured facts',main),

 e('piMd','plaus','/<skill>',main),
 e('canon','sync'), e('sync','piDir'), e('subagents','piDir',null,{variant:'dashed'}),
 e('plaus','scout'), e('scout','grapher'), e('grapher','screener'), e('screener','plausGate'), e('plausGate','pool',null,{variant:'security'}),
 e('ingest','ingestAgent'), e('ingestAgent','guidance'),
 e('delib','delibCli'), e('delibCli','delibGate'), e('delibGate','delibPub',null,{variant:'security'}), e('delibPub','proposals'),
 e('grapher','delibPub','atlas.json',{variant:'dashed'}),
 e('expDelib','expVal'), e('expVal','expGate'), e('expGate','expPub',null,{variant:'security'}), e('expPub','experiments'),
 e('impl','implBuild'), e('implBuild','implWalk'), e('implWalk','implGate'), e('implGate','repo',null,{variant:'security'}),
 e('expImpl','expBuild'), e('expBuild','expWalk'), e('expWalk','expImplGate'),
 e('kaggle','accCli'), e('accCli','store'),
 e('remote','readiness'), e('readiness','remoteCli',null,{variant:'security'}), e('remoteCli','inbox'),
 e('store','remoteCli','credentials',{variant:'dashed'}),
 e('pw','insumos'), e('insumos','redactor'), e('redactor','contract'), e('contract','style'), e('style','grounding'),
 e('pw','paperCli','delegates',{variant:'dashed'}),
 e('paperCli','diagram'), e('diagram','figAud'), e('figAud','figRev'),
 e('grounding','paper','sections',{variant:'dashed'}),
 e('audit','auditRep'), e('auditRep','report'),
];
const lanes=[
 ['pi','0 · Pi harness'], ['plaus','1 · Plausibility'],['ingest','2 · Ingestion'],['delib','3 · Proposal deliberation'],
 ['impl','4 · Implementation (proof of concept)'],['expdelib','5 · Experimental deliberation'],['expimpl','6 · Experimental implementation'],
 ['creds','7 · Credentials'],['remote','8 · Remote execution'],['write','9 · Writing'],['figs','10 · Figures and grounding'],['out','11 · Paper'],
 ['audit','Transversal · Audit']].map(([id,label])=>({id,label}));

const laneIdx=Object.fromEntries(lanes.map((l,i)=>[l.id,i]));
const components=nodes.map(({lane,col,width,...r})=>({...r,row:laneIdx[lane],col,size:[182,58]}));
const connections=edges.map(({role,...r})=>r);
const boundaries=lanes.map(l=>({kind:'region',label:l.label,wraps:nodes.filter(x=>x.lane===l.id).map(x=>x.id)}));
const doc={schema_version:1,diagram_type:'architecture',meta:{
  title:'Papersmith AI in Pi — commands, skills and agents',
  quality_profile:'showcase',
  output:'docs/diagrams/papersmith-pi-flow.html',
  repository:{url:'https://github.com/LIAUNAL/papersmith-ai',provider:'github',link_mode:'web',revision:'1cf76a0dc810e162fa70c6726990f87d63fc56db'},
  legend:{mode:'auto',entries:{frontend:{label:'Pi command /skill'},backend:{label:'Pi subagent'},messagebus:{label:'CLI'},security:{label:'Gate (human)'},database:{label:'Artifact on disk'},external:{label:'Pi harness'}}}
 },
 layout:{mode:'grid',origin:[40,48],cols:6,cellW:182,cellH:58,gapX:21,gapY:62},
 components, boundaries, connections,
 cards:[
  {dot:'cyan',title:'How Pi sees it',items:['.pi/APPEND_SYSTEM.md is the system prompt: Pi appends it to the project one','/<skill> = .pi/prompts/<skill>.md: it loads the SKILL.md and passes $ARGUMENTS','The 19 .pi/agents/ are projected from .claude/agents/; Pi core has no subagents, so they need pi-subagents','Each agent declares tools (read, find, grep, write, edit, bash, mcp) and its stretch','refuse-offpath-push.js intercepts bash tool_call; it is a warning that fails open, not a gate']},
  {dot:'emerald',title:'Harness commands',items:['npm run setup:harnesses — links .pi/skills -> ../skills','python scripts/sync-repo-harness.py — regenerates .pi/prompts, .pi/agents, .pi/extensions (--check detects drift)','papersmith init · status · ingest · deliberate · implement · run · remote · audit · ui','npm run test:all — the quality gate']},
  {dot:'violet',title:'Per-skill CLIs',items:['paper-ingestion: python scripts/setup_env.py install','deliberation: node skills/<skill>/cli.mjs --serve','the proposal graph: merge_proposal_sky.py → check_atlas.py → render_atlas.py','implementation: implementation_cli.py materialize · verify · fidelity · audit · step','kaggle-accounts: accounts_cli.py list · discover · validate · remove · materialize','remote-execution: remote_cli.py submit · status · poll · fetch · readiness …','paper-writing: paper_cli.py status · plan · write · verify … (28 verbs)','figure-review: review_cli.py probe · raster · skill-audit: audit_cli.py']},
  {dot:'amber',title:'Flow rules',items:['The order is optional: each skill refuses with a code when its input is missing','Starting with /plausibility, before ingestion, is the recommendation','No walk can launch a campaign: the operator authorizes it','contract-auditor, redactor and style-sampler have no code path: the orchestrator launches them and write judges','/figure-review and /skill-audit only report; they never repair']}
 ]};
const out = path.resolve(process.argv[2] || fileURLToPath(new URL('./candidate.json', import.meta.url)));
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, JSON.stringify(doc, null, 1));
console.log(`candidate: ${out}`);
