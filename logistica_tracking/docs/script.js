/* ============================================================
   Logistica Tracking API — docs behaviour
   Scroll-spy nav, on-this-page builder, endpoint search, and a
   small JSON/HTTP highlighter. No dependencies.
   ============================================================ */
(function () {
  "use strict";

  /* ── syntax highlighting ─────────────────────────────────
     Deliberately small: highlights JSON and the request line of
     HTTP snippets. Tokenising via one pass over string literals
     first, so keywords inside strings are never re-marked.
  */
  function escapeHtml(s) {
    return s.replace(/[&<>]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c];
    });
  }

  function highlight(raw) {
    var out = "";
    var i = 0;

    while (i < raw.length) {
      var ch = raw[i];

      // line comment
      if (ch === "/" && raw[i + 1] === "/") {
        var eol = raw.indexOf("\n", i);
        if (eol === -1) eol = raw.length;
        out += '<span class="tok-com">' + escapeHtml(raw.slice(i, eol)) + "</span>";
        i = eol;
        continue;
      }

      // string literal (may be a key if followed by a colon)
      if (ch === '"') {
        var j = i + 1;
        while (j < raw.length && !(raw[j] === '"' && raw[j - 1] !== "\\")) j++;
        var lit = raw.slice(i, j + 1);
        var after = raw.slice(j + 1).match(/^\s*:/);
        out += '<span class="' + (after ? "tok-key" : "tok-str") + '">' + escapeHtml(lit) + "</span>";
        i = j + 1;
        continue;
      }

      // HTTP verb at start of a line
      if (/[A-Z]/.test(ch)) {
        var verb = raw.slice(i).match(/^(GET|POST|PATCH|PUT|DELETE)\b/);
        var atLineStart = i === 0 || raw[i - 1] === "\n";
        if (verb && atLineStart) {
          out += '<span class="tok-verb">' + verb[0] + "</span>";
          i += verb[0].length;
          continue;
        }
      }

      // literals
      var lit2 = raw.slice(i).match(/^(true|false|null)\b/);
      if (lit2) {
        out += '<span class="tok-bool">' + lit2[0] + "</span>";
        i += lit2[0].length;
        continue;
      }

      // numbers
      var num = raw.slice(i).match(/^-?\d+(\.\d+)?/);
      if (num && !/[\w.]/.test(raw[i - 1] || "")) {
        out += '<span class="tok-num">' + num[0] + "</span>";
        i += num[0].length;
        continue;
      }

      out += escapeHtml(ch);
      i++;
    }
    return out;
  }

  document.querySelectorAll("pre > code").forEach(function (el) {
    if (el.dataset.nohl !== undefined) return;
    el.innerHTML = highlight(el.textContent);
  });

  /* ── build "on this page" from h2/h3 ─────────────────────── */
  var tocList = document.getElementById("tocList");
  var headings = [].slice.call(document.querySelectorAll(".content h2[id], .content h3[id]"));

  if (tocList) {
    headings.forEach(function (h) {
      var a = document.createElement("a");
      a.href = "#" + h.id;
      a.textContent = h.textContent.replace(/#$/, "").trim();
      if (h.tagName === "H3") a.className = "sub";
      tocList.appendChild(a);
    });
  }

  /* ── scroll-spy across sidebar + toc ─────────────────────
     Tracks the heading nearest the top of the viewport rather than
     using IntersectionObserver ratios, so short sections at the end
     of the page still register when the page can't scroll further.
  */
  var sidebarLinks = [].slice.call(document.querySelectorAll(".sidebar a[href^='#']"));
  var tocLinks = function () { return [].slice.call(document.querySelectorAll(".toc a")); };

  function byHash(links, hash) {
    return links.filter(function (a) { return a.getAttribute("href") === hash; });
  }

  var spyTargets = [].slice.call(
    document.querySelectorAll(".content h2[id], .content h3[id], .content [id].endpoint")
  );

  var ticking = false;
  function updateActive() {
    ticking = false;
    var top = window.scrollY + 96;
    var current = null;

    for (var i = 0; i < spyTargets.length; i++) {
      if (spyTargets[i].offsetTop <= top) current = spyTargets[i];
      else break;
    }
    // at the very bottom, force the last target active
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 4) {
      current = spyTargets[spyTargets.length - 1] || current;
    }
    if (!current) return;

    var hash = "#" + current.id;
    sidebarLinks.concat(tocLinks()).forEach(function (a) { a.classList.remove("active"); });
    byHash(sidebarLinks, hash).concat(byHash(tocLinks(), hash)).forEach(function (a) {
      a.classList.add("active");
    });
  }

  window.addEventListener("scroll", function () {
    if (!ticking) { window.requestAnimationFrame(updateActive); ticking = true; }
  }, { passive: true });
  window.addEventListener("resize", updateActive, { passive: true });
  updateActive();

  /* ── endpoint search ─────────────────────────────────────
     Filters sidebar links in place and hides any group whose
     children all dropped out, so the nav never shows an empty header.
  */
  var search = document.getElementById("search");
  if (search) {
    search.addEventListener("input", function () {
      var q = search.value.trim().toLowerCase();

      document.querySelectorAll(".nav-group").forEach(function (group) {
        var links = [].slice.call(group.querySelectorAll("a"));
        var anyVisible = false;

        links.forEach(function (a) {
          var hit = !q || a.textContent.toLowerCase().indexOf(q) !== -1;
          a.hidden = !hit;
          if (hit) anyVisible = true;
        });

        group.hidden = !anyVisible;
      });
    });

    // "/" focuses search, Escape clears it
    document.addEventListener("keydown", function (e) {
      var typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName);
      if (e.key === "/" && !typing) {
        e.preventDefault();
        search.focus();
      } else if (e.key === "Escape" && document.activeElement === search) {
        search.value = "";
        search.dispatchEvent(new Event("input"));
        search.blur();
      }
    });
  }

  /* ── mobile nav ──────────────────────────────────────────── */
  var toggle = document.getElementById("navToggle");
  var sidebar = document.getElementById("sidebar");
  var scrim = document.getElementById("scrim");

  function setNav(open) {
    sidebar.classList.toggle("open", open);
    scrim.hidden = !open;
    toggle.setAttribute("aria-expanded", String(open));
  }

  if (toggle) {
    toggle.addEventListener("click", function () {
      setNav(!sidebar.classList.contains("open"));
    });
    scrim.addEventListener("click", function () { setNav(false); });
    sidebar.addEventListener("click", function (e) {
      if (e.target.tagName === "A" && window.innerWidth <= 860) setNav(false);
    });
  }
})();
