const target = document.querySelector('[data-markdown-target]');
const buttons = [...document.querySelectorAll('[data-markdown-source]')];

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
    document.title = `${button.textContent.trim()} — MPVRP-CC`;
    history.replaceState(null, '', `#${button.dataset.documentId}`);
  } catch (error) {
    target.innerHTML = `<p class="rounded-xl bg-red-50 p-4 text-red-700">Unable to load the Markdown source: ${error.message}</p>`;
  }
}

buttons.forEach((button) => button.addEventListener('click', () => renderMarkdown(button)));
const requested = location.hash.slice(1);
renderMarkdown(buttons.find((button) => button.dataset.documentId === requested) || buttons[0]);

document.querySelector('[data-print-document]')?.addEventListener('click', () => window.print());
