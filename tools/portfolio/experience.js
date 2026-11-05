// Photograph assets are embedded once in the standalone HTML, then reused.
$$('img[data-asset]').forEach(image=>{image.src=ASSETS[image.dataset.asset];image.decoding='async'});
// Only visible scenes animate. Each control keeps its existing pointer behavior.
const sceneObserver=new IntersectionObserver(entries=>entries.forEach(entry=>entry.target.classList.toggle('is-near',entry.isIntersecting)),{rootMargin:'90px'});
$$('.hero,.sensory-section,.project-card').forEach(scene=>sceneObserver.observe(scene));
const finePointer=matchMedia('(hover:hover) and (pointer:fine)');
$$('.project-visual').forEach(visual=>{
 let pending=0,pointer=null;
 function paintPointer(){pending=0;if(!pointer||motionPaused||!finePointer.matches)return;const rect=visual.getBoundingClientRect(),x=Math.max(0,Math.min(1,(pointer.x-rect.left)/rect.width)),y=Math.max(0,Math.min(1,(pointer.y-rect.top)/rect.height));visual.style.setProperty('--light-x',x*100+'%');visual.style.setProperty('--light-y',y*100+'%');if(!visual.querySelector('.image-divider')){visual.style.setProperty('--tilt-x',(x-.5)*6+'deg');visual.style.setProperty('--tilt-y',(.5-y)*5+'deg')}}
 visual.addEventListener('pointermove',event=>{if(event.pointerType==='touch'||!finePointer.matches)return;pointer={x:event.clientX,y:event.clientY};if(!pending)pending=requestAnimationFrame(paintPointer)},{passive:true});
 visual.addEventListener('pointerleave',()=>{pointer=null;if(pending)cancelAnimationFrame(pending);pending=0;visual.style.setProperty('--tilt-x','0deg');visual.style.setProperty('--tilt-y','0deg');visual.style.setProperty('--light-x','30%');visual.style.setProperty('--light-y','15%')});
});
let scrollPaint=0;
function paintScroll(){scrollPaint=0;const root=document.documentElement,range=root.scrollHeight-innerHeight;root.style.setProperty('--reading-progress',range>0?scrollY/range:0);const gallery=$('.sensory-section'),rect=gallery.getBoundingClientRect();if(!motionPaused&&rect.bottom>0&&rect.top<innerHeight){const travel=Math.max(-18,Math.min(18,(innerHeight*.5-rect.top-rect.height*.5)*.035));gallery.style.setProperty('--parallax',travel+'px')}else gallery.style.setProperty('--parallax','0px')}
function queueScroll(){if(!scrollPaint)scrollPaint=requestAnimationFrame(paintScroll)}
addEventListener('scroll',queueScroll,{passive:true});addEventListener('resize',queueScroll,{passive:true});$('#motion-button').addEventListener('click',queueScroll);reducedMotion.addEventListener('change',queueScroll);document.addEventListener('visibilitychange',()=>{document.body.classList.toggle('tab-hidden',document.hidden)});queueScroll();
$$('.sensory-tile').forEach(link=>link.addEventListener('click',event=>{if(event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;const target=$(link.getAttribute('href'));if(target?.hidden)$('[data-filter="all"]').click()}));
