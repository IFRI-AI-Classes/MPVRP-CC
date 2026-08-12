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
