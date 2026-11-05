import fs from 'node:fs';
const locales=JSON.parse(fs.readFileSync('source-locales.json','utf8'));
const additions=JSON.parse(fs.readFileSync('project-additions.json','utf8'));
const interactions=JSON.parse(fs.readFileSync('interaction-copy.json','utf8'));
for(const [lang,extra] of Object.entries(additions.locales)){
  const locale=locales[lang];
  locale.project_names.push(...extra.project_names);
  locale.project_descriptions.push(...extra.project_descriptions);
  Object.assign(locale.art,extra.art);
  locale.projects_intro=extra.projects_intro;
  locale.nav[0]=extra.nav;
}
const editorial=JSON.parse(fs.readFileSync('editorial-copy.json','utf8'));
for(const [lang,copy] of Object.entries(editorial)){Object.assign(locales[lang],copy.source);Object.assign(locales[lang].art,copy.art)}
const assets=Object.fromEntries(['coast','botanical'].map(name=>[name,'data:image/webp;base64,'+fs.readFileSync('assets/'+name+'.webp').toString('base64')]));
const template=fs.readFileSync('index.template.html','utf8').replace('__EXPERIENCE_CSS__',()=>fs.readFileSync('experience.css','utf8')).replace('__EXPERIENCE_SCRIPT__',()=>fs.readFileSync('experience.js','utf8')).replace('__EDITORIAL_COPY__',()=>JSON.stringify(editorial).replaceAll('<','\\u003c')).replace('__VISUAL_ASSETS__',()=>JSON.stringify(assets));
const mobius=fs.readFileSync('mobius-reference.svg','utf8');
fs.mkdirSync('dist',{recursive:true});
fs.writeFileSync('dist/index.html',template.replace('__SOURCE_LOCALES__',JSON.stringify(locales).replaceAll('<','\\u003c')).replace('__PROJECT_ADDITIONS__',JSON.stringify(additions).replaceAll('<','\\u003c')).replace('__INTERACTION_COPY__',JSON.stringify(interactions).replaceAll('<','\\u003c')).replace('__MOBIUS_REFERENCE__',mobius));
console.log('Built self-contained portfolio: dist/index.html');
