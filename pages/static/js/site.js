document.querySelectorAll('[data-menu-button]').forEach((button) => {
  button.addEventListener('click', () => {
    const menu = document.querySelector('[data-mobile-menu]');
    menu?.classList.toggle('hidden');
    button.setAttribute('aria-expanded', String(!menu?.classList.contains('hidden')));
  });
});

document.querySelectorAll('[data-year]').forEach((node) => {
  node.textContent = String(new Date().getFullYear());
});

const truckIcon = `
  <span class="brand-icon" aria-hidden="true">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 6h11v10H3zM14 9h3l4 4v3h-7z"/><circle cx="7" cy="18" r="2"/><circle cx="18" cy="18" r="2"/>
    </svg>
  </span>`;

document.querySelectorAll('[data-site-brand]').forEach((brand) => {
  brand.innerHTML = truckIcon;
});

const githubIcon = `<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .7a11.5 11.5 0 0 0-3.64 22.4c.58.1.79-.25.79-.56v-2.23c-3.22.7-3.9-1.37-3.9-1.37-.52-1.34-1.28-1.7-1.28-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.7 1.26 3.36.96.1-.75.4-1.26.73-1.55-2.57-.29-5.27-1.28-5.27-5.69 0-1.26.45-2.28 1.19-3.09-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.16 1.18a10.9 10.9 0 0 1 5.76 0c2.2-1.49 3.16-1.18 3.16-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.83 1.19 3.09 0 4.42-2.7 5.39-5.28 5.68.42.36.78 1.06.78 2.14v3.17c0 .31.21.67.8.56A11.5 11.5 0 0 0 12 .7Z"/></svg>`;
const mailIcon = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/></svg>`;

document.querySelectorAll('[data-site-footer]').forEach((footer) => {
  footer.innerHTML = `
    <div class="mx-auto max-w-7xl px-5 py-10 lg:px-8">
      <div class="grid gap-8 md:grid-cols-[1fr_auto] md:items-start">
        <div>
          <p class="font-display text-lg font-semibold text-slate-900">MPVRP-CC</p>
          <p class="mt-2 max-w-xl text-sm leading-6 text-slate-500">A research benchmark for multi-product vehicle routing with changeover costs.</p>
          <a class="site-footer-link mt-4 text-sm font-semibold" href="https://github.com/uac-rrteam" target="_blank" rel="noopener">${githubIcon} UAC Ratheil Research Team</a>
        </div>
        <div>
          <p class="text-xs font-bold uppercase tracking-widest text-slate-400">Principal contributors</p>
          <div class="mt-3 grid gap-2.5 text-sm">
            <div class="contributor-row"><span class="font-medium text-slate-700">Rosas Behoundja</span><span class="contributor-actions"><a class="contributor-icon contributor-icon--github" href="https://github.com/rosasbehoundja" target="_blank" rel="noopener" aria-label="GitHub de Rosas Behoundja" title="GitHub">${githubIcon}</a><a class="contributor-icon contributor-icon--email" href="mailto:perrierosas@gmail.com" aria-label="Envoyer un email à Rosas Behoundja" title="perrierosas@gmail.com">${mailIcon}</a></span></div>
            <div class="contributor-row"><span class="font-medium text-slate-700">Ratheil Houndji</span><span class="contributor-actions"><a class="contributor-icon contributor-icon--github" href="https://github.com/ratheilh" target="_blank" rel="noopener" aria-label="GitHub de Ratheil Houndji" title="GitHub">${githubIcon}</a><a class="contributor-icon contributor-icon--email" href="mailto:vratheilhoundji@gmail.com" aria-label="Envoyer un email à Ratheil Houndji" title="vratheilhoundji@gmail.com">${mailIcon}</a></span></div>
          </div>
        </div>
      </div>
      <div class="mt-8 border-t border-slate-200 pt-5 text-xs text-slate-400">© ${new Date().getFullYear()} MPVRP-CC · UAC Ratheil Research Team · Apache-2.0.</div>
    </div>`;
});
