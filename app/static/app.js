// Species123 client behaviour: theme, menu, compare tray, search selection, lazy taxonomy tree.
(function () {
  'use strict';
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }
  };
  var MAX = 4;

  function toast(msg) {
    var el = document.createElement('div');
    el.className = 'toast';
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(function () { el.remove(); }, 1600);
  }

  // theme
  function paintTheme() {
    var dark = document.documentElement.getAttribute('data-theme') === 'dark';
    $$('[data-theme-icon]').forEach(function (el) { el.hidden = (el.dataset.themeIcon === 'dark') !== dark; });
  }
  $$('[data-theme-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      try { localStorage.setItem('species123.theme', next); } catch (e) {}
      paintTheme();
    });
  });
  paintTheme();

  // mobile menu
  var menu = $('[data-menu]');
  $$('[data-menu-toggle]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var open = menu.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
  });

  // 工具 dropdown: close on an outside click or Escape
  var navMenu = $('[data-nav-menu]');
  if (navMenu) {
    document.addEventListener('click', function (e) { if (!navMenu.contains(e.target)) navMenu.open = false; });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') navMenu.open = false; });
  }

  // compare tray (ids in localStorage, mirrored into nav links)
  function tray() { return store.get('species123.compare', store.get('taien.compare', [])).slice(0, MAX); }
  function setTray(ids) {
    var uniq = ids.filter(function (x, i) { return x && ids.indexOf(x) === i; }).slice(-MAX);
    store.set('species123.compare', uniq);
    paintTray();
  }
  function compareUrl(ids) { return '/compare' + (ids.length ? '?ids=' + ids.join(',') : ''); }
  function paintTray() {
    var ids = tray();
    $$('[data-compare-count]').forEach(function (el) { el.textContent = ids.length; el.hidden = !ids.length; });
    $$('[data-compare-link]').forEach(function (a) { a.href = compareUrl(ids); });
    $$('[data-add-compare]').forEach(function (btn) {
      if (ids.indexOf(btn.dataset.addCompare) >= 0) {
        var span = $('span', btn);
        if (span) span.textContent = btn.dataset.labelIn;
      }
    });
  }
  $$('[data-add-compare]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var ids = tray();
      if (ids.indexOf(btn.dataset.addCompare) < 0) ids.push(btn.dataset.addCompare);
      setTray(ids);
      location.href = compareUrl(tray());
    });
  });

  var cmpPage = $('[data-compare-page]');
  if (cmpPage) {
    var pageIds = cmpPage.dataset.ids ? cmpPage.dataset.ids.split(',') : [];
    if (!pageIds.length && tray().length && !/[?&]ids=/.test(location.search)) {
      location.replace(compareUrl(tray()));
      return;
    }
    store.set('species123.compare', pageIds);
    var diff = $('[data-diff-only]');
    if (diff) diff.addEventListener('change', function () { $('[data-compare-grid]').classList.toggle('diff-only', diff.checked); });
  }
  paintTray();

  // search: auto-submit facets, row click, selection → compare
  var form = $('[data-search-form]');
  if (form) {
    $$('.sidebar input[type=checkbox]', form).forEach(function (cb) {
      cb.addEventListener('change', function () { form.submit(); });
    });
    var selected = [];
    var label = $('[data-selected-label]');
    var btn = $('[data-compare-selected]');
    var paintSel = function () {
      label.textContent = selected.length ? label.dataset.tpl.replace('{n}', selected.length) : label.dataset.empty;
      btn.disabled = selected.length < 2;
      $$('tr[data-row]').forEach(function (tr) { tr.classList.toggle('is-selected', selected.indexOf(tr.dataset.row) >= 0); });
    };
    $$('[data-select]').forEach(function (cb) {
      cb.addEventListener('change', function () {
        var id = cb.dataset.select;
        if (cb.checked) {
          if (selected.length >= MAX) { cb.checked = false; return; }
          selected.push(id);
        } else {
          selected = selected.filter(function (x) { return x !== id; });
        }
        paintSel();
      });
    });
    if (btn) btn.addEventListener('click', function () { setTray(selected); location.href = compareUrl(selected); });
    $$('tr[data-href]').forEach(function (tr) {
      tr.addEventListener('click', function (e) {
        if (e.target.closest('a, label, input, button')) return;
        location.href = tr.dataset.href;
      });
    });
  }

  // taxonomy tree: lazy expand / collapse
  var tree = $('[data-tree]');
  function rowsAfter(row) {
    var depth = +row.dataset.depth, out = [], el = row.nextElementSibling;
    while (el && +el.dataset.depth > depth) { out.push(el); el = el.nextElementSibling; }
    return out;
  }
  function setOpen(row, open) {
    row.setAttribute('aria-expanded', String(open));
    var b = $('[data-tree-toggle]', row);
    if (b) b.setAttribute('aria-expanded', String(open));
  }
  if (tree) {
    tree.addEventListener('click', function (e) {
      var b = e.target.closest('[data-tree-toggle]');
      if (!b) return;
      e.preventDefault();
      var row = b.closest('.tree-row');
      if (row.getAttribute('aria-expanded') === 'true') {
        rowsAfter(row).forEach(function (el) { el.remove(); });
        setOpen(row, false);
        return;
      }
      b.disabled = true;
      fetch(b.dataset.treeToggle, { headers: { 'X-Requested-With': 'fetch' } })
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
        .then(function (html) { row.insertAdjacentHTML('afterend', html); setOpen(row, true); })
        .catch(function () { toast('⚠'); })
        .then(function () { b.disabled = false; });
    });
    var collapse = $('[data-tree-collapse]');
    if (collapse) collapse.addEventListener('click', function () {
      $$('[data-depth]', tree).forEach(function (el) {
        if (+el.dataset.depth > 0) el.remove();
        else setOpen(el, false);
      });
    });
    var sel = $('.tree-row.is-selected', tree);
    if (sel) tree.scrollTop = sel.offsetTop - tree.clientHeight / 2;
  }

  // field guide tabs (all panels stay visible without JS)
  var tabs = $('[data-tabs]');
  var guide = $('.guide');
  if (tabs && guide) {
    var ids = $$('[data-tab]', tabs).map(function (a) { return a.dataset.tab; });
    var show = function (id) {
      if (ids.indexOf(id) < 0) id = ids[0];
      $$('[data-tab]', tabs).forEach(function (a) { a.setAttribute('aria-selected', String(a.dataset.tab === id)); });
      $$('[data-tab-panel]', guide).forEach(function (p) {
        var on = p.dataset.tabPanel === id;
        p.classList.toggle('is-active', on);
        // tab-deferred photos: fetch the files only once their tab is shown
        if (on) $$('img[data-src]', p).forEach(function (img) { img.src = img.dataset.src; img.removeAttribute('data-src'); });
      });
    };
    guide.classList.add('is-tabbed');
    tabs.addEventListener('click', function (e) {
      var a = e.target.closest('[data-tab]');
      if (!a) return;
      e.preventDefault();
      history.replaceState(null, '', '#' + a.dataset.tab);
      show(a.dataset.tab);
    });
    // the header photo opens the photos tab
    $$('[data-goto-tab]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        history.replaceState(null, '', '#' + a.dataset.gotoTab);
        show(a.dataset.gotoTab);
        tabs.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
    show(location.hash.slice(1));
  }

  // copy citation
  $$('[data-copy]').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var done = function () { toast(btn.dataset.copied); };
      if (navigator.clipboard) navigator.clipboard.writeText(btn.dataset.copy).then(done, function () {});
    });
  });
})();
