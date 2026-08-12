const target = document.querySelector('[data-markdown-target]');
const buttons = [...document.querySelectorAll('[data-markdown-source]')];
const toc = document.querySelector('[data-toc-target]');

function slugify(value) {
  return value
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/(^-|-$)/g, '');
}

function buildTableOfContents(documentId) {
  if (!target || !toc) return;
  const headings = [...target.querySelectorAll('h2, h3')];
  toc.innerHTML = '';

  headings.forEach((heading, index) => {
    const baseId = slugify(heading.textContent) || `section-${index + 1}`;
    heading.id = `${documentId}-${baseId}`;
    heading.classList.add('scroll-mt-28');

    const link = document.createElement('a');
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent;
    link.className = heading.tagName === 'H3' ? 'toc-link toc-link--nested' : 'toc-link';
    toc.appendChild(link);
  });

  document.querySelector('[data-toc-shell]')?.classList.toggle('hidden', headings.length === 0);
}

async function renderMarkdown(button) {
  if (!target || !button) return;
  buttons.forEach((item) => {
    const active = item === button;
    item.classList.toggle('bg-blue-600', active);
    item.classList.toggle('text-white', active);
    item.classList.toggle('bg-white', !active);
    item.classList.toggle('text-slate-600', !active);
    item.setAttribute('aria-selected', String(active));
  });
  target.innerHTML = '<p class="text-slate-500">Loading documentation…</p>';
  try {
    const response = await fetch(button.dataset.markdownSource);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const markdown = await response.text();
    target.innerHTML = marked.parse(markdown, { gfm: true });
    buildTableOfContents(button.dataset.documentId);
    document.title = `${button.textContent.trim()} — MPVRP-CC`;
    history.replaceState(null, '', `#${button.dataset.documentId}`);
  } catch (error) {
    target.innerHTML = `<p class="rounded-xl bg-red-50 p-4 text-red-700">Unable to load the documentation: ${error.message}</p>`;
  }
}

buttons.forEach((button) => button.addEventListener('click', () => renderMarkdown(button)));
const requested = location.hash.slice(1).split('-')[0];
renderMarkdown(buttons.find((button) => button.dataset.documentId === requested) || buttons[0]);

document.querySelector('[data-print-document]')?.addEventListener('click', () => window.print());
