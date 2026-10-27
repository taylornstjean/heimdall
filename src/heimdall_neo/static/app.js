// lenis for smooth scrolling
import Lenis from 'https://esm.sh/lenis@1.3.26';

document.querySelectorAll('.panel-content').forEach(wrapper => {
    new Lenis({
        wrapper,
        content: wrapper.querySelector('.panel-inner'),
        autoRaf: true,
    });
});

// table sorting by clicking headers
const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: 'base' });
const table = document.querySelector('#neocp-table');
const headers = [...table.querySelectorAll('thead th')];

function sortTable() {
    const col = headers.findIndex(h => h.hasAttribute('aria-sort'));
    if (col === -1) return;
    const asc = headers[col].getAttribute('aria-sort') === 'ascending';
    const tbody = table.tBodies[0];
    const rows = [...tbody.rows].sort((a, b) => {
        const r = collator.compare(
            a.cells[col].textContent.trim(),
            b.cells[col].textContent.trim()
        );
        return asc ? r : -r;
    });
    tbody.append(...rows);
}

headers.forEach(th => {
    th.addEventListener('click', () => {
        const asc = th.getAttribute('aria-sort') !== 'ascending';
        headers.forEach(h => h.removeAttribute('aria-sort'));
        th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
        sortTable();
    });
});

// auto reload every 30 seconds, this is maximum API call rate so is fine
const REFRESH_MS = 30_000;
const countdown = document.querySelector('#countdown');
let nextRefresh = Date.now() + REFRESH_MS;
let refreshing = false;

async function refresh() {
    refreshing = true;
    countdown.textContent = 'updating...';
    try {
        const res = await fetch(location.href);
        if (res.ok) {
            const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
            for (const sel of ['#neocp-table tbody', '#right-panel .panel-inner']) {
                document.querySelector(sel).innerHTML = doc.querySelector(sel).innerHTML;
            }
            sortTable();
        }
    } catch (e) {
        console.error(e);
    } finally {
        refreshing = false;
        nextRefresh = Date.now() + REFRESH_MS;
    }
}

function tick() {
    if (refreshing) return;
    const remaining = nextRefresh - Date.now();
    if (remaining <= 0) {
        refresh();
        return;
    }
    countdown.textContent = `${Math.ceil(remaining / 1000)}s`;
}

setInterval(tick, 250);
tick();

// highlight cards when hovering on table and vice versa
function highlight(e, on) {
    const src = e.target.closest('[data-desig]');
    if (!src || src.contains(e.relatedTarget)) return;
    document.querySelectorAll(`[data-desig="${CSS.escape(src.dataset.desig)}"]`)
        .forEach(el => el.classList.toggle('highlight', on));
}

document.addEventListener('mouseover', e => highlight(e, true));
document.addEventListener('mouseout', e => highlight(e, false));
