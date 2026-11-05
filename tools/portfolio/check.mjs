import fs from 'node:fs';
import vm from 'node:vm';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const html=fs.readFileSync('dist/index.html','utf8');
assert(!html.includes('__SOURCE_LOCALES__'),'Unresolved build data');
assert(!html.includes('__PROJECT_ADDITIONS__'),'Unresolved project additions');
assert(!html.includes('__INTERACTION_COPY__'),'Unresolved interaction copy');
for(const key of ['__EDITORIAL_COPY__','__VISUAL_ASSETS__','__EXPERIENCE_CSS__','__EXPERIENCE_SCRIPT__'])assert(!html.includes(key),'Unresolved visual experience data: '+key);
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
const dictionaries=script.slice(script.indexOf('const ORIGINAL='),script.indexOf('let language='));
const context=vm.createContext({});
vm.runInContext(dictionaries+';this.data={ORIGINAL,UI,PROJECTS,ASSETS};',context);
const {ORIGINAL,UI,PROJECTS,ASSETS}=context.data;
for(const name of ['coast','botanical']){
 assert(ASSETS[name].startsWith('data:image/webp;base64,'),'Photograph must be available offline');
 assert.equal(Buffer.compare(Buffer.from(ASSETS[name].split(',')[1],'base64'),fs.readFileSync('assets/'+name+'.webp')),0,'Embedded photograph differs from selected asset');
}
const languages=['ko','en','ja','zh','fr','es'];
assert.deepEqual(Object.keys(ORIGINAL).sort(),languages.slice().sort());
assert.equal(PROJECTS.length,8);
assert.deepEqual(Array.from(PROJECTS,p=>p.repo),['Illustracy','Scanner','Chordity','efx','Upscaly','Film_Sim','MacGuard','Photo_Scorer']);
const required=[...html.matchAll(/data-ui="([^"]+)"/g)].map(m=>m[1]).filter(key=>!key.includes('${'));
const uiKeys=Object.keys(UI.en).sort();
for(const lang of languages){
 assert.deepEqual(Object.keys(UI[lang]).sort(),uiKeys,`UI schema differs: ${lang}`);
 for(const key of required)assert(UI[lang][key],`Missing UI ${lang}.${key}`);
 assert.equal(ORIGINAL[lang].project_names.length,8);
 assert.equal(ORIGINAL[lang].project_descriptions.length,8);
 assert.equal(UI[lang].categories.length,8);
 assert.equal(UI[lang].photoMetricNames.length,7);
 assert.equal(UI[lang].demoInstructions.length,8);
 assert.equal(ORIGINAL[lang].principles.length,20);
 for(const p of PROJECTS)assert(lang==='en'||ORIGINAL[lang].art[p.banner],`Missing banner ${lang}.${p.id}`);
}
assert(!/<script[^>]+src="https?:/i.test(html),'Unexpected external script');
for(const tag of html.matchAll(/<link\b[^>]*>/gi)){
 if(/href="https?:/i.test(tag[0]))assert(/rel="canonical"/i.test(tag[0]),'Unexpected external runtime dependency');
}
assert(html.includes('<link rel="canonical" href="https://yeon.at/portfolio/">'));
assert(html.includes('<meta name="robots" content="index,follow">'));
assert(!fs.existsSync('dist/qa.html'),'Remove temporary QA harness before packaging');
console.log('PASS: JavaScript syntax, six locale schemas, 48 translated project banners, eight repository links, seven photo criteria, no external runtime dependencies, public canonical URL, release contents.');

// Compare the embedded model against geometry read from the source repository.
const reference=fs.readFileSync('mobius-reference.svg','utf8');
const provenance=JSON.parse(fs.readFileSync('mobius-reference.json','utf8'));
const hash=value=>crypto.createHash('sha256').update(value).digest('hex');
assert.equal(hash(reference),provenance.asset_sha256,'Reference asset changed');
const faces=[...reference.matchAll(/<g data-material-face="([^"]+)" clip-path="([^"]+)"><g transform="([^"]+)">/g)].map(m=>m.slice(1,4));
assert.equal(faces.length,provenance.face_count);
assert.equal(hash(JSON.stringify(faces)),provenance.geometry_sha256,'Projected geometry or UV orientation differs from the repository');
const ids=[...reference.matchAll(/\bid="([^"]+)"/g)].map(m=>m[1]);
assert.equal(new Set(ids).size,ids.length,'Duplicate SVG IDs');
for(const m of reference.matchAll(/(?:url\(#([^)]*)\)|href="#([^"]+)")/g))assert(ids.includes(m[1]||m[2]),`Missing SVG reference ${m[1]||m[2]}`);
const flows=[...reference.matchAll(/<animateTransform attributeName="transform" type="translate" values="([^"]+)" dur="([^"]+)"/g)];
assert.equal(flows.length,2);
for(const m of flows){assert.equal(m[1],provenance.material_values);assert.equal(m[2],provenance.material_duration)}
assert(html.includes(reference.trim()),'Release does not contain the original SVG');
assert(!html.includes('__MOBIUS_REFERENCE__'));
assert(!/href="https?:/i.test(reference),'External SVG dependency');
assert(!reference.includes('hero-orbit'),'Whole-model orbit was reintroduced');
console.log('PASS: all 720 repository faces, original UV direction and depth order, complete inline SVG references, original positive-X material motion.');

// Run the actual timeline controller against the SVG API contract.
let seeks=[],paints=[],paused=false;const handlers={};
const fakeSvg={pauseAnimations(){paused=true},setCurrentTime(t){seeks.push(t)},addEventListener(n,f){handlers[n]=f},setPointerCapture(){}};
const fakeRenderer={draw(offset){paints.push(offset)},ready:{then(){return {catch(){}}}}};
Object.assign(context,{$:()=>fakeSvg,createBeltRenderer:()=>fakeRenderer,IntersectionObserver:class{observe(){}},requestAnimationFrame(){},motionPaused:false,document:{hidden:false,addEventListener(){}}});
const controller=script.split('// MOBIUS_CONTROLLER_BEGIN')[1].split('// MOBIUS_CONTROLLER_END')[0];
vm.runInContext(controller,context);
assert(paused,'SVG native timeline must be controlled by the page');
assert.equal(seeks.at(-1),0);
assert.equal(paints.at(-1),0);
vm.runInContext('for(let now=100;now<=160;now+=10)tick(now);',context);assert(Math.abs(seeks.at(-1)-.06)<1e-9,'Source timeline must advance forward at its native speed');
assert(Math.abs(paints.at(-1)-.06/5.6*1200)<1e-8,'Visible material renderer was not advanced');
context.motionPaused=true;const hold=seeks.at(-1),paintHold=paints.at(-1);vm.runInContext('tick(220);tick(280);',context);assert.equal(seeks.at(-1),hold,'Pause failed');assert.equal(paints.at(-1),paintHold,'Material painting ignored pause');
handlers.keydown({key:'ArrowRight',preventDefault(){}});assert(seeks.at(-1)>hold,'ArrowRight must advance source flow');
const beforeDrag=seeks.at(-1);handlers.pointerdown({clientX:50,pointerId:1});handlers.pointermove({clientX:110});assert(seeks.at(-1)>beforeDrag,'Pointer drag failed');handlers.pointerup();
vm.runInContext('advanceBelt(-1000);drawMobius();',context);assert(seeks.at(-1)>=0&&seeks.at(-1)<provenance.controller_period,'Backward scrubbing must wrap all source tracks without a jump');assert(paints.at(-1)>=0&&paints.at(-1)<1200);
console.log('PASS: direct material painting, native-speed forward flow, pause, keyboard/drag scrubbing, common-period reverse wrapping.');

// Exercise display-rate interpolation and delayed-frame recovery, rather than
// asserting only that an animation callback was registered.
for(const hz of [30,60,120,144]){
  const time=vm.runInContext(`(()=>{const clock=createBeltInterpolator();let time=0;for(let frame=1;frame<=${hz};frame++)time=clock.advance(1/${hz});return time})()`,context);
  assert(Math.abs(time-1)<1e-8,`${hz} Hz changed the native belt speed`);
}
const interpolated=vm.runInContext('createBeltInterpolator().advance(1/240)',context);
assert(Math.abs(interpolated-1/240)<1e-10,'Fractional frames must interpolate instead of repeating a 120 Hz state');
const late=vm.runInContext('(()=>{const clock=createBeltInterpolator();const before=clock.advance(1/120),after=clock.advance(.12);let recovered=after;for(let i=0;i<120;i++)recovered=clock.advance(1/120);return {jump:after-before,recovered}})()',context);
assert(late.jump<=.04+1e-9,'A dropped frame caused an immediate timeline jump');
assert(Math.abs(late.recovered-(1+1/120+.12))<1e-8,'Late-frame time was not gradually recovered');
const noDebt=vm.runInContext('(()=>{const clock=createBeltInterpolator();clock.advance(.2);clock.seek(10);return clock.advance(1/120)})()',context);
assert(Math.abs(noDebt-(10+1/120))<1e-9,'Seeking must clear delayed-frame recovery');
const slowCadence=vm.runInContext('(()=>{const clock=createBeltInterpolator();let time=0;for(let i=0;i<100;i++)time=clock.advance(1/20);return time})()',context);
assert(Math.abs(slowCadence-5)<1e-8,'A consistently slower display must not accumulate slow-motion drift');
const seam=vm.runInContext('(()=>{const clock=createBeltInterpolator(251.999);return clock.advance(1/240)})()',context);
assert(seam>252&&seam<252.01,'Interpolation must cross the common-period seam forward without reversing');
context.motionPaused=false;
const frameStart=paints.length;
vm.runInContext('beltTime=0;beltInterpolator.seek(0);lastFrame=0;needsDraw=false;tick(1000);for(let i=1;i<=120;i++)tick(1000+i*1000/120);',context);
assert.equal(paints.length-frameStart,120,'120 Hz callbacks must each paint a new interpolated frame');
context.document.hidden=true;const hiddenHold=seeks.at(-1);vm.runInContext('tick(8000)',context);
context.document.hidden=false;vm.runInContext('tick(9000)',context);assert.equal(seeks.at(-1),hiddenHold,'Returning from a hidden tab must not jump ahead');
console.log('PASS: 30/60/120/144 Hz native speed, fractional-frame interpolation, bounded late-frame correction, debt reset, all 120 Hz frames painted, hidden-tab resume.');
