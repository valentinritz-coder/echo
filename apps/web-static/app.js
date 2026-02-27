// Intensifie légèrement le halo quand le champ principal reçoit le focus.
const ta = document.getElementById("echo-input");

function autosize(el) {
  el.style.height = "auto";

  const styles = window.getComputedStyle(el);
  const maxH = parseFloat(styles.maxHeight) || Infinity;

  const next = Math.min(el.scrollHeight, maxH);
  el.style.height = next + "px";

  // si on dépasse max, on laisse scroll interne
  el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
}

if (ta) {
  autosize(ta);
  ta.addEventListener("input", () => autosize(ta));
  window.addEventListener("resize", () => autosize(ta));
}