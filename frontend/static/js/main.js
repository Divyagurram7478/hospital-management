// main.js - generic utilities
document.addEventListener('DOMContentLoaded', function(){
  const maps = document.querySelectorAll('.map-embed');
  // lazy load embed if present
  maps.forEach(m => {
    const src = m.dataset.src;
    if(src){
      const iframe = document.createElement('iframe');
      iframe.src = src;
      iframe.width = '100%';
      iframe.height = '300';
      iframe.style.border = 0;
      iframe.loading = 'lazy';
      m.appendChild(iframe);
    }
  });
});
