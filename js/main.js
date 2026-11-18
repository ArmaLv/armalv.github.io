(() => {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const LEAVES = Array.from(
    { length: 10 },
    (_, i) => `Assets/leaves/leaf-${String(i + 1).padStart(2, "0")}.svg`
  );

  const initLeaves = () => {
    const host = document.getElementById("petals");
    if (!host) return;

    const rnd = (a, b) => a + Math.random() * (b - a);
    const base = innerWidth < 640 ? 18 : 34;
    // still fall when reduced-motion is set, just fewer and calmer
    const count = reduceMotion ? Math.round(base * 0.6) : base;

    for (let i = 0; i < count; i++) {
      const size = rnd(16, 40);
      const fall = rnd(9, 20);
      const delay = -rnd(0, 20);
      const sway = rnd(3.5, 6.5);
      const amp = rnd(18, 70); 
      const spin = rnd(4, 11);
      const spinDelay = -rnd(0, 11);

      const petal = document.createElement("span");
      petal.className = "petal";
      petal.style.cssText = `--x:${rnd(-2, 100).toFixed(2)}vw;--size:${size.toFixed(0)}px;--fall:${fall.toFixed(1)}s;--delay:${delay.toFixed(1)}s;`;

      const drift = document.createElement("span");
      drift.className = "petal__drift";
      drift.style.cssText = `--sway:${sway.toFixed(1)}s;--amp:${amp.toFixed(0)}px;animation-delay:${delay.toFixed(1)}s;`;

      const spinEl = document.createElement("span");
      spinEl.className = "petal__spin";
      spinEl.style.cssText = `--spin:${spin.toFixed(1)}s;--spinDelay:${spinDelay.toFixed(1)}s;--dir:${Math.random() < 0.5 ? "normal" : "reverse"};`;

      const img = document.createElement("img");
      img.src = LEAVES[(Math.random() * LEAVES.length) | 0];
      img.alt = "";
      img.loading = "lazy";
      img.style.setProperty("--op", rnd(0.72, 1).toFixed(2));

      spinEl.appendChild(img);
      drift.appendChild(spinEl);
      petal.appendChild(drift);
      host.appendChild(petal);
    }
  };

  const initScroll = () => {
    const toc = document.getElementById("toc");
    const bud = document.querySelector(".stem__bud");

    const onScroll = () => {
      const y = window.scrollY;
      const max = document.documentElement.scrollHeight - innerHeight;
      const pct = max > 0 ? y / max : 0;
      if (toc) toc.classList.toggle("is-scrolled", y > 40);
      if (bud) bud.style.transform = `translate(-50%, ${pct * (innerHeight - 20)}px) rotate(${pct * 180}deg)`;
    };

    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  };

  const initReveals = (root = document) => {
    const items = root.querySelectorAll("[data-reveal]");
    items.forEach((el) => {
      const d = el.getAttribute("data-delay");
      if (d) el.style.setProperty("--d", d);
    });

    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    items.forEach((el) => io.observe(el));
  };

  const LANG_COLORS = {
    "C#": "#9a7bb0", "C++": "#c76b86", C: "#8a7d72",
    Python: "#6f8f9a", JavaScript: "#c99a4b", TypeScript: "#6b86b0",
    HTML: "#c47a5a", CSS: "#8a6fa0", SCSS: "#b06f8c",
    Shell: "#8aa072", Lua: "#6f72a0", Rust: "#b58a6f",
    Go: "#5a95a0", Java: "#a67b52", ShaderLab: "#7d8a72", HLSL: "#9aae72",
  };
  const PALETTE = ["#e49bb0", "#8aa072", "#b8863f", "#9a7bb0"];
  const colorFor = (lang, i) => LANG_COLORS[lang] || PALETTE[i % PALETTE.length];

  const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"];

  const esc = (s = "") =>
    String(s).replace(/[&<>"']/g, (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
    );

  const buildPlate = (p, i) => {
    const a = document.createElement("a");
    a.className = "plate reveal";
    a.setAttribute("data-reveal", "");
    a.href = p.url || "#";
    a.target = "_blank";
    a.rel = "noopener";

    const stars = p.stars ? `<span class="plate__stars">❀ ${p.stars}</span>` : "";
    const tags = (p.tags || [])
      .slice(0, 6)
      .map((t) => `<span class="tag">${esc(t)}</span>`)
      .join("");

    const langs = p.languages || [];
    const bar = langs
      .map((l, k) => `<span class="langs__seg" style="width:${l.percent}%;background:${colorFor(l.name, k)}"></span>`)
      .join("");
    const legend = langs
      .slice(0, 4)
      .map((l, k) => `<span><i class="langs__dot" style="background:${colorFor(l.name, k)}"></i>${esc(l.name)} ${l.percent}%</span>`)
      .join("");

    const readme = p.readme ? `<p class="plate__readme">${esc(p.readme)}</p>` : "";

    a.innerHTML = `
      <div class="plate__top">
        <span class="plate__no">Plate ${ROMAN[i] || i + 1}</span>
        ${stars}
      </div>
      <h3 class="plate__name">${esc(p.name)}</h3>
      <p class="plate__desc">${esc(p.description || "A quiet work, still taking shape.")}</p>
      ${tags ? `<div class="plate__tags">${tags}</div>` : ""}
      ${langs.length ? `<div class="langs"><div class="langs__bar">${bar}</div><div class="langs__legend">${legend}</div></div>` : ""}
      ${readme}
      <span class="plate__foot">read on <span class="arrow">→</span></span>
    `;
    return a;
  };

  const initWorks = async () => {
    const grid = document.getElementById("works-grid");
    const empty = document.getElementById("works-empty");
    if (!grid) return;

    try {
      const res = await fetch("data/projects.json", { cache: "no-cache" });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      const projects = Array.isArray(data) ? data : data.projects || [];

      if (!projects.length) {
        if (empty) empty.textContent = "No plates yet — run the Python tool to press one.";
        return;
      }
      if (empty) empty.remove();

      const frag = document.createDocumentFragment();
      projects.forEach((p, i) => frag.appendChild(buildPlate(p, i)));
      grid.appendChild(frag);
      initReveals(grid);
    } catch (err) {
      if (empty) empty.textContent = "Couldn't reach the archive of plates.";
      console.warn("[works] failed to load data/projects.json:", err);
    }
  };

  const start = () => {
    initLeaves();
    initScroll();
    initReveals();
    initWorks();
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
