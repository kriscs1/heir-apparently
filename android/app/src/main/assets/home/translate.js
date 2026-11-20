// Other languages (data/Lang/<code>.txt, tools/lang.py): the page in the player's own. English is the key, so a word
// the catalogue hasn't got yet stays English. The start screen and the game both load this (a plain script:
// window.DSLang): the start screen's words come in lang.js, the game's from web/assets/lang/<code>.json. What's drawn
// on the game's canvas is said through tr (web/js/util.js coined); what's on the page, as it's put there (watch).
(function () {
  "use strict";
  const LANGS = [["en", "English"], ["es", "Español"], ["de", "Deutsch"], ["fr", "Français"], ["pt", "Português (Brasil)"],
    ["zh", "简体中文"], ["ja", "日本語"], ["ko", "한국어"]];
  // (a hole in a line: {1}, {2}... where the code puts something in, or a script's $Player.Name)
  const HOLE = /\{\d+\}|\$[A-Za-z]+\.[A-Za-z0-9_.()']*[A-Za-z0-9_)]/g;
  const SKIP = new Set(["SCRIPT", "STYLE", "TEXTAREA", "INPUT", "CODE", "CANVAS"]);
  const ATTRS = ["title", "placeholder", "aria-label", "alt"];
  let code = "en", exact = null, starts = new Map(), loose = [], cache = new Map();

  const norm = (s) => s.replace(/\s+/g, " ").trim();
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  function pattern(en, said) {
    const holes = en.match(HOLE);
    const bits = en.split(HOLE);
    // (a hole joined to a word is the word's ending, and may be empty: English's plural "s", "thing{3}"; or what
    // follows it, from a space or a stop: "maintenance{1}" with ": why". Never more of a sentence, or "{1} Shard{2}"
    // would take any line with "Shard" in it)
    const re = new RegExp("^" + bits.map((b, i) => (i ? (/[A-Za-z]$/.test(bits[i - 1]) ? "(\\S*?|[^A-Za-z].*?)" : "(.+?)") : "") +
      esc(b)).join("") + "$");
    const p = { re, holes, said };
    const head = bits[0].slice(0, 3);
    if (head.length === 3) {
      if (!starts.has(head)) starts.set(head, []);
      starts.get(head).push(p);
    } else loose.push(p);
  }

  function add(words) {
    if (!words) return;
    if (!exact) exact = new Map();
    for (const [en, said] of Object.entries(words)) {
      const k = norm(en);
      HOLE.lastIndex = 0;
      if (HOLE.test(k)) pattern(k, said);
      else exact.set(k, said);
    }
    cache = new Map();
  }

  function fill(p, m) {
    let out = p.said;
    p.holes.forEach((h, i) => {
      const v = m[i + 1];
      out = out.split(h).join(exact.get(v) ?? v);     // (a name in it said too: "You catch a {1}." with Trout)
      // (and a plural said the language's way: {3:/n} is "" for one, "n" for more)
      out = out.replace(new RegExp("\\{" + h.slice(1, -1) + ":([^{}/]*)/([^{}]*)\\}", "g"), (_, one, more) => v ? more : one);
    });
    return out;
  }

  function look(text) {
    const t = norm(text);
    if (!t) return text;
    let said = exact.get(t);
    if (said === undefined) {
      for (const p of (starts.get(t.slice(0, 3)) || []).concat(loose)) {
        const m = p.re.exec(t);
        if (m) { said = fill(p, m); break; }
      }
    }
    if (said === undefined) return text;
    const lead = /^\s*/.exec(text)[0], tail = /\s*$/.exec(text)[0];       // (its spaces kept: "Gold: " then a number)
    return lead + said + tail;
  }

  // text in the player's language, if the catalogue has it (cached: the game draws the same words every frame)
  function tr(text) {
    if (!exact || typeof text !== "string" || !text) return text;
    let r = cache.get(text);
    if (r !== undefined) return r;
    r = look(text);
    if (cache.size > 8000) cache = new Map();
    cache.set(text, r);
    cache.set(r, r);                                 // (said once is said: fitText, then drawText, says it again)
    return r;
  }

  // ----- the page: its words said as they're put there, and again whenever they change. Each keeps its English
  // (orig), so another language is said from that; what we wrote ourselves (mine) isn't taken for new English.
  const orig = new WeakMap(), mine = new WeakMap();
  function said(key, now, put) {
    let en = now;
    const was = mine.get(key);
    if (was !== undefined && was === now) en = orig.get(key);
    orig.set(key, en);
    const s = tr(en);
    mine.set(key, s);
    if (s !== now) put(s);
  }
  const attrKeys = new WeakMap();
  function attrKey(el, a) {
    let k = attrKeys.get(el);
    if (!k) attrKeys.set(el, k = {});
    return k[a] || (k[a] = {});
  }

  function sayNode(n) {
    if (n.nodeType === 3) {
      if (/[A-Za-z]/.test(n.data)) said(n, n.data, (s) => { n.data = s; });
      return;
    }
    if (n.nodeType !== 1 || SKIP.has(n.tagName) || n.getAttribute("translate") === "no") return;
    if (n.tagName === "OPTION" && !n.hasAttribute("value")) n.setAttribute("value", n.textContent);   // (its value stays English)
    for (const a of ATTRS) {
      const v = n.getAttribute(a);
      if (v) said(attrKey(n, a), v, (s) => n.setAttribute(a, s));
    }
    for (let c = n.firstChild; c; c = c.nextSibling) sayNode(c);
  }

  function inNo(n) {
    for (let e = n.nodeType === 1 ? n : n.parentElement; e; e = e.parentElement) {
      if (SKIP.has(e.tagName) || e.getAttribute("translate") === "no") return true;
    }
    return false;
  }

  let watcher = null, watched = null;
  function watch(root) {
    root = root || document.body;
    if (!root) return;
    watched = root;
    sayNode(root);
    if (watcher) return;
    watcher = new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === "childList") { for (const n of m.addedNodes) if (!inNo(n)) sayNode(n); }
        else if (!inNo(m.target)) sayNode(m.target);              // (its words changed, or a title)
      }
    });
    watcher.observe(root, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ATTRS });
  }

  // The language a player has: what they chose, else their device's if the game has it, else English
  function pick(chosen) {
    const have = LANGS.map((l) => l[0]);
    if (chosen && have.includes(chosen)) return chosen;
    for (const l of navigator.languages || [navigator.language || ""]) {
      const c = String(l).slice(0, 2).toLowerCase();
      if (have.includes(c)) return c;
    }
    return "en";
  }

  // Another language (words: its catalogue): the canvas says it from the next frame, the page at once
  function use(c, words) {
    code = c || "en";
    exact = null; starts = new Map(); loose = []; cache = new Map();
    if (code !== "en") add(words || {});
    document.documentElement.lang = code;
    if (watched) sayNode(watched);
  }

  window.DSLang = { LANGS, tr, add, use, watch, pick, get code() { return code; } };
})();
