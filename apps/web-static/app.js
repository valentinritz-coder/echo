// -----------------------------
// Textarea autosize
// -----------------------------
const textarea = document.getElementById("echo-input");

function autosize(el) {
  if (!el) return;

  el.style.height = "auto";

  const styles = window.getComputedStyle(el);
  const maxH = Number.parseFloat(styles.maxHeight) || Infinity;

  const nextH = Math.min(el.scrollHeight, maxH);
  el.style.height = `${nextH}px`;
  el.style.overflowY = el.scrollHeight > maxH ? "auto" : "hidden";
}

if (textarea) {
  autosize(textarea);
  textarea.addEventListener("input", () => autosize(textarea));
  window.addEventListener("resize", () => autosize(textarea));
}

// -----------------------------
// Fake data (50 memories)
// -----------------------------
const memories = [
  { id: 1, date: "1950-01-14", text: "Une lettre pliée en quatre, retrouvée dans un vieux livre.", audio: false, image: true },
  { id: 2, date: "1951-07-03", text: "Premier jour de travail. Impression de porter un costume trop grand.", audio: true, image: false },
  { id: 3, date: "1952-11-26", text: "Un hiver sec. Les pas craquent sur le givre.", audio: false, image: false },
  { id: 4, date: "1954-05-19", text: "Une photo floue mais on reconnaît les sourires.", audio: false, image: true },
  { id: 5, date: "1956-09-08", text: "On a parlé de partir. On est restés.", audio: true, image: false },
  { id: 6, date: "1958-03-27", text: "Une chanson à la radio. Toujours la même émotion.", audio: true, image: false },

  { id: 7, date: "1960-06-12", text: "Un carnet neuf. La promesse de mieux faire.", audio: false, image: true },
  { id: 8, date: "1961-10-02", text: "Dimanche au soleil. Rien d’urgent, et ça fait du bien.", audio: false, image: false },
  { id: 9, date: "1963-02-15", text: "Un silence lourd, puis une décision simple.", audio: true, image: false },
  { id: 10, date: "1964-08-21", text: "Une route poussiéreuse. On rigole pour rien.", audio: false, image: true },
  { id: 11, date: "1966-12-05", text: "On s’est promis de se revoir vite. Mensonge innocent.", audio: false, image: false },
  { id: 12, date: "1969-04-30", text: "Un anniversaire sans gâteau. Mais une vraie paix.", audio: true, image: true },

  { id: 13, date: "1970-01-09", text: "Nouveau départ. Même ville, autre regard.", audio: false, image: false },
  { id: 14, date: "1972-07-18", text: "Le goût des tomates du jardin. Impossible à reproduire.", audio: false, image: true },
  { id: 15, date: "1973-10-11", text: "Une dispute bête, et puis on s’est excusés.", audio: true, image: false },
  { id: 16, date: "1975-03-26", text: "Un train en retard. Ça a changé la journée, et la suite.", audio: false, image: false },
  { id: 17, date: "1977-09-02", text: "Une photo de groupe. Certains noms s’effacent.", audio: false, image: true },
  { id: 18, date: "1979-12-23", text: "Veille de fête. On fait semblant d’aller bien. On y arrive.", audio: true, image: false },

  { id: 19, date: "1980-05-06", text: "Une carte postale: trois lignes, et ça suffit.", audio: false, image: true },
  { id: 20, date: "1981-11-28", text: "Un pull qui gratte, mais c’était un cadeau sincère.", audio: false, image: false },
  { id: 21, date: "1983-02-19", text: "Une cassette audio. La voix a vieilli, pas l’intention.", audio: true, image: false },
  { id: 22, date: "1984-08-14", text: "Vacances simples. Une baignade froide, un rire net.", audio: false, image: true },
  { id: 23, date: "1986-10-30", text: "On apprend une nouvelle et tout devient plus petit.", audio: true, image: false },
  { id: 24, date: "1989-04-01", text: "Poisson d’avril. On s’est fait avoir comme des débutants.", audio: false, image: false },

  { id: 25, date: "1990-06-25", text: "Un objet perdu, retrouvé au bon moment.", audio: false, image: true },
  { id: 26, date: "1992-01-13", text: "Une page tournée. Pas proprement, mais définitivement.", audio: true, image: false },
  { id: 27, date: "1993-09-07", text: "On a repeint une pièce. L’odeur est restée des semaines.", audio: false, image: false },
  { id: 28, date: "1995-12-09", text: "Soir d’hiver, fenêtre embuée, tête pleine.", audio: true, image: false },
  { id: 29, date: "1998-06-12", text: "Un souvenir ancien, juste pour tester le drill-down.", audio: false, image: false },
  { id: 30, date: "1999-11-20", text: "Fin de décennie. On fait semblant de comprendre l’avenir.", audio: false, image: true },

  { id: 31, date: "2001-03-05", text: "Premier email important. On imprime quand même, par réflexe.", audio: false, image: false },
  { id: 32, date: "2003-07-22", text: "Un été trop chaud. L’air vibrait au-dessus de la route.", audio: false, image: true },
  { id: 33, date: "2004-10-16", text: "Une photo prise trop vite, mais parfaite.", audio: false, image: true },
  { id: 34, date: "2006-02-09", text: "On s’est parlé tard. Les mots étaient plus vrais à minuit.", audio: true, image: false },
  { id: 35, date: "2008-09-30", text: "Un grand changement. Sur le moment, ça ressemble à une panne.", audio: true, image: false },
  { id: 36, date: "2009-12-31", text: "Minuit. On se souhaite le mieux, sans savoir comment.", audio: true, image: true },

  { id: 37, date: "2010-04-17", text: "Une promenade sans but. La meilleure idée de la semaine.", audio: false, image: false },
  { id: 38, date: "2012-06-29", text: "Un message simple: 't’es là ?' et tout change.", audio: true, image: false },
  { id: 39, date: "2013-11-08", text: "On a appris à dire non. Lentement, mais enfin.", audio: false, image: false },
  { id: 40, date: "2015-01-23", text: "Une photo de neige. Le monde avait l’air plus silencieux.", audio: false, image: true },
  { id: 41, date: "2017-08-12", text: "Une soirée dehors. On parle comme si on avait le temps.", audio: true, image: false },
  { id: 42, date: "2019-10-05", text: "Une vieille chanson ressort. Elle sait encore viser juste.", audio: true, image: false },

  { id: 43, date: "2020-03-19", text: "Le temps s’est étiré. On a dû inventer un rythme.", audio: false, image: false },
  { id: 44, date: "2021-05-27", text: "Une photo de famille. On regarde plus les détails que les visages.", audio: false, image: true },
  { id: 45, date: "2022-09-14", text: "Une note vocale envoyée sans réfléchir. C’était la bonne.", audio: true, image: false },
  { id: 46, date: "2023-12-02", text: "Une fin d’année dense. Pas mauvaise. Dense.", audio: false, image: false },
  { id: 47, date: "2024-02-18", text: "Un repas simple. Le genre qui remet les choses en place.", audio: false, image: true },
  { id: 48, date: "2025-07-09", text: "Une décision prise sans drame. Juste une évidence.", audio: true, image: false },

  { id: 49, date: "2026-01-10", text: "J’ai retrouvé une photo de famille ce matin.", audio: true, image: true },
  { id: 50, date: "2026-02-27", text: "Aujourd’hui, j’ai envie de laisser une trace claire.", audio: true, image: true },
];

// -----------------------------
// Sidebar drill-down timeline
// -----------------------------
const sidebarList = document.getElementById("sidebar-list");

// state: [{ level, key }]
const navStack = [];

// utils
function parseYear(dateStr) {
  const y = Number(String(dateStr || "").slice(0, 4));
  return Number.isFinite(y) ? y : null;
}

function rangeLabel(start, end) {
  return `${start} – ${end}`;
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function dotSummary(m) {
  const dots = [];
  if (m.text && m.text.trim()) dots.push("•");
  if (m.audio) dots.push("◍");
  if (m.image) dots.push("◼︎");
  return dots.join(" ");
}

// grouping
function groupByCentury(items, nowYear) {
  const map = new Map();

  for (const m of items) {
    const y = parseYear(m.date);
    if (y == null) continue;

    const start = Math.floor(y / 100) * 100;
    const key = start;

    let end = start + 99;
    if (start <= nowYear && nowYear <= end) end = nowYear; // cut current century

    if (!map.has(key)) map.set(key, { start, end, items: [] });
    map.get(key).items.push(m);
  }

  return Array.from(map.values()).sort((a, b) => b.start - a.start);
}

function groupByDecade(items, centuryStart) {
  const map = new Map();

  for (const m of items) {
    const y = parseYear(m.date);
    if (y == null) continue;
    if (y < centuryStart || y > centuryStart + 99) continue;

    const start = Math.floor(y / 10) * 10;
    const key = start;

    if (!map.has(key)) map.set(key, { start, end: start + 9, items: [] });
    map.get(key).items.push(m);
  }

  return Array.from(map.values()).sort((a, b) => b.start - a.start);
}

function groupByYear(items, decadeStart) {
  const map = new Map();

  for (const m of items) {
    const y = parseYear(m.date);
    if (y == null) continue;
    if (y < decadeStart || y > decadeStart + 9) continue;

    if (!map.has(y)) map.set(y, { year: y, items: [] });
    map.get(y).items.push(m);
  }

  return Array.from(map.values()).sort((a, b) => b.year - a.year);
}

// DOM helpers
function addListItem({ title, subtitle = "", dots = null, className = "", onClick }) {
  const li = document.createElement("li");
  li.className = `sidebar-item ${className}`.trim();

  li.innerHTML = `
    <a class="sidebar-link" href="#">
      <div class="sidebar-row">
        <span class="sidebar-date">${escapeHtml(title)}</span>
        ${dots ? `<span class="sidebar-dots" aria-hidden="true">${escapeHtml(dots)}</span>` : ""}
      </div>
      ${subtitle ? `<div class="sidebar-text">${escapeHtml(subtitle)}</div>` : ""}
    </a>
  `;

  li.querySelector("a").addEventListener("click", (e) => {
    e.preventDefault();
    onClick?.();
  });

  sidebarList.appendChild(li);
}

function addBackItem() {
  addListItem({
    className: "is-back",
    title: `
      <span class="sidebar-back-inner">
        <span class="sidebar-back-arrow" aria-hidden="true">
          <svg width="10" viewBox="0 0 12 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M0.245636 8.59302C-0.0818787 8.2655 -0.0818787 7.7345 0.245636 7.40698L4.43892 3.2137C4.76643 2.88619 5.29744 2.88619 5.62495 3.2137C5.95247 3.54122 5.95247 4.07223 5.62495 4.39974L2.86335 7.16134H10.9025C11.3657 7.16134 11.7412 7.53682 11.7412 8C11.7412 8.46318 11.3657 8.83866 10.9025 8.83866H2.86335L5.62495 11.6003C5.95247 11.9278 5.95247 12.4588 5.62495 12.7863C5.29744 13.1138 4.76643 13.1138 4.43892 12.7863L0.245636 8.59302Z" fill="currentColor"></path>
          </svg>
        </span>
      </span>
    `.trim(),
    // on injecte déjà du HTML ci-dessus: pas d'escape ici
    // donc on bypass en passant directement dans innerHTML ci-dessous
    onClick: () => {
      navStack.pop();
      renderSidebarList();
    },
  });
}

// rendu: on veut éviter d’escape le back (il contient du SVG)
// donc on le construit à la main ici
function renderBackRow() {
  const li = document.createElement("li");
  li.className = "sidebar-item is-back";
  li.innerHTML = `
    <a class="sidebar-link sidebar-back-link" href="#" aria-label="Retour">
      <div class="sidebar-row" style="margin-bottom:0">
        <span class="sidebar-back-inner">
          <span class="sidebar-back-arrow" aria-hidden="true">
            <svg width="10" viewBox="0 0 12 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M0.245636 8.59302C-0.0818787 8.2655 -0.0818787 7.7345 0.245636 7.40698L4.43892 3.2137C4.76643 2.88619 5.29744 2.88619 5.62495 3.2137C5.95247 3.54122 5.95247 4.07223 5.62495 4.39974L2.86335 7.16134H10.9025C11.3657 7.16134 11.7412 7.53682 11.7412 8C11.7412 8.46318 11.3657 8.83866 10.9025 8.83866H2.86335L5.62495 11.6003C5.95247 11.9278 5.95247 12.4588 5.62495 12.7863C5.29744 13.1138 4.76643 13.1138 4.43892 12.7863L0.245636 8.59302Z" fill="currentColor"></path>
            </svg>
          </span>
        </span>
      </div>
    </a>
  `;
  li.querySelector("a").addEventListener("click", (e) => {
    e.preventDefault();
    navStack.pop();
    renderSidebarList();
  });
  sidebarList.appendChild(li);
}

function renderSidebarList() {
  if (!sidebarList) return;

  const all = (window.memories || memories || []).slice();
  const nowYear = new Date().getFullYear();

  sidebarList.innerHTML = "";

  // back full-width (if in sub-level)
  if (navStack.length > 0) renderBackRow();

  // level 0: centuries
  if (navStack.length === 0) {
    const centuries = groupByCentury(all, nowYear);
    for (const c of centuries) {
      addListItem({
        title: rangeLabel(c.start, c.end),
        subtitle: `${c.items.length} souvenirs`,
        dots: null,
        onClick: () => {
          navStack.push({ level: "century", key: c.start });
          renderSidebarList();
        },
      });
    }
    return;
  }

  const top = navStack[navStack.length - 1];

  // level 1: decades
  if (top.level === "century") {
    const decades = groupByDecade(all, top.key);
    for (const d of decades) {
      addListItem({
        title: rangeLabel(d.start, d.end),
        subtitle: `${d.items.length} souvenirs`,
        dots: null,
        onClick: () => {
          navStack.push({ level: "decade", key: d.start });
          renderSidebarList();
        },
      });
    }
    return;
  }

  // level 2: years
  if (top.level === "decade") {
    const years = groupByYear(all, top.key);
    for (const y of years) {
      addListItem({
        title: String(y.year),
        subtitle: `${y.items.length} souvenirs`,
        dots: null,
        onClick: () => {
          navStack.push({ level: "year", key: y.year });
          renderSidebarList();
        },
      });
    }
    return;
  }

  // level 3: items
  if (top.level === "year") {
    const items = all
      .filter((m) => parseYear(m.date) === top.key)
      .sort((a, b) => String(b.date).localeCompare(String(a.date)));

    for (const m of items) {
      addListItem({
        title: m.date,
        subtitle: m.text || "",
        dots: dotSummary(m),
        onClick: () => {
          // TODO: sélectionner et afficher à droite
        },
      });
    }
  }
}

// init
renderSidebarList();
