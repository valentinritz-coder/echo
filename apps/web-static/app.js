// Intensifie légèrement le halo quand le champ principal reçoit le focus.
const input = document.querySelector('#echo-input');

if (input) {
  input.addEventListener('focus', () => {
    document.body.classList.add('is-focused');
  });

  input.addEventListener('blur', () => {
    document.body.classList.remove('is-focused');
  });
}
