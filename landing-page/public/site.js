const tabs = [...document.querySelectorAll('[data-panel]')];
const tabList = document.querySelector('#audit-tabs');

function activateTab(tab, moveFocus = false) {
  for (const item of tabs) {
    const selected = item === tab;
    item.setAttribute('aria-selected', String(selected));
    item.tabIndex = selected ? 0 : -1;
    document.getElementById(item.dataset.panel).hidden = !selected;
  }
  if (moveFocus) tab.focus();
}

// Without JavaScript, every example remains readable in document order.
tabList.setAttribute('role', 'tablist');
for (const tab of tabs) {
  tab.setAttribute('role', 'tab');
  tab.setAttribute('aria-controls', tab.dataset.panel);
  const panel = document.getElementById(tab.dataset.panel);
  panel.setAttribute('role', 'tabpanel');
  panel.tabIndex = 0;
  tab.addEventListener('click', () => activateTab(tab));
  tab.addEventListener('keydown', (event) => {
    const index = tabs.indexOf(tab);
    let target;
    if (event.key === 'ArrowRight') target = tabs[(index + 1) % tabs.length];
    if (event.key === 'ArrowLeft') target = tabs[(index - 1 + tabs.length) % tabs.length];
    if (event.key === 'Home') target = tabs[0];
    if (event.key === 'End') target = tabs[tabs.length - 1];
    if (!target) return;
    event.preventDefault();
    activateTab(target, true);
  });
}
activateTab(tabs[0]);

// Animate only arriving content; no loops, scroll listeners, or hidden copy.
if ('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('arrived');
      observer.unobserve(entry.target);
    }
  }, { threshold: 0.12 });
  document.querySelectorAll('.reveal').forEach((element) => observer.observe(element));
  window.addEventListener('pagehide', () => observer.disconnect(), { once: true });
}
