document.addEventListener('DOMContentLoaded', () => {

    // ========================================
    // CATEGORY FILTER & LIVE SEARCH
    // ========================================
    const categoryButtons = document.querySelectorAll('#category-filters .category');
    const searchInput = document.getElementById('search-input');
    const activitiesGrid = document.getElementById('activities-grid');
    const countText = document.getElementById('activity-count-text');

    let currentCategory = 'all';
    let searchQuery = '';

    function filterActivities() {
        const cards = activitiesGrid.querySelectorAll('.activity');
        let visibleCount = 0;

        cards.forEach(card => {
            const cardCategory = (card.getAttribute('data-category') || '').toLowerCase();
            const title = (card.getAttribute('data-title') || '').toLowerCase();
            const location = (card.getAttribute('data-location') || '').toLowerCase();
            const desc = (card.getAttribute('data-desc') || '').toLowerCase();

            const matchesCategory = (currentCategory === 'all' || cardCategory === currentCategory);
            const matchesSearch = !searchQuery ||
                title.includes(searchQuery) ||
                location.includes(searchQuery) ||
                desc.includes(searchQuery) ||
                cardCategory.includes(searchQuery);

            if (matchesCategory && matchesSearch) {
                card.style.display = 'flex';
                card.style.flexDirection = 'column';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });

        // Handle empty state
        let emptyState = document.getElementById('no-activities-found');
        if (visibleCount === 0) {
            if (!emptyState) {
                emptyState = document.createElement('div');
                emptyState.id = 'no-activities-found';
                emptyState.className = 'empty-state';
                emptyState.innerHTML = `
                    <h3>No matching activities found</h3>
                    <p>Try searching for different keywords or explore other categories.</p>
                `;
                activitiesGrid.appendChild(emptyState);
            }
            emptyState.style.display = 'block';
        } else {
            if (emptyState) emptyState.style.display = 'none';
        }

        if (countText) {
            if (currentCategory === 'all' && !searchQuery) {
                countText.textContent = `Showing ${visibleCount} active campus ${visibleCount === 1 ? 'activity' : 'activities'}.`;
            } else {
                countText.textContent = `Found ${visibleCount} ${visibleCount === 1 ? 'activity' : 'activities'}.`;
            }
        }
    }

    categoryButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            categoryButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentCategory = btn.getAttribute('data-category').toLowerCase();
            filterActivities();
        });
    });

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value.trim().toLowerCase();
            filterActivities();
        });
    }

    // Run initial filter to set count text
    filterActivities();
});


// ========================================
// PEOPLE SEARCH (same search box, finds usernames)
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    const panel = document.getElementById('people-panel');
    const input = document.getElementById('search-input');
    if (!panel || !input) return;

    const list = document.getElementById('people-results');
    const csrf = document.querySelector('#people-csrf [name=csrfmiddlewaretoken]').value;
    const urls = {
        search: panel.dataset.searchUrl,
        add: panel.dataset.addUrl,
        accept: panel.dataset.acceptUrl,
        remove: panel.dataset.removeUrl,
    };
    const userUrl = (template, id) => template.replace(/0\/$/, `${id}/`);

    function button(label, kind, url, confirmText) {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = url;
        if (confirmText) form.addEventListener('submit', e => { if (!confirm(confirmText)) e.preventDefault(); });
        const q = input.value.trim();
        const next = location.pathname + (q ? `?q=${encodeURIComponent(q)}` : '');
        form.innerHTML = `<input type="hidden" name="csrfmiddlewaretoken"><input type="hidden" name="next"><button type="submit" class="fbtn ${kind}"></button>`;
        form.querySelector('[name=csrfmiddlewaretoken]').value = csrf;
        form.querySelector('[name=next]').value = next;
        form.querySelector('button').textContent = label;
        return form;
    }

    function tag(text, cls) {
        const span = document.createElement('span');
        span.className = 'fstate ' + (cls || '');
        span.textContent = text;
        return span;
    }

    function render(people) {
        list.replaceChildren();
        for (const p of people) {
            const row = document.createElement('div');
            row.className = 'person';
            row.innerHTML = '<div class="person-avatar"></div><div class="person-info"><div class="person-name"></div><div class="person-sub"></div></div><div class="person-actions"></div>';
            row.querySelector('.person-avatar').textContent = p.initial;
            row.querySelector('.person-name').textContent = p.username;
            row.querySelector('.person-sub').textContent = p.subtitle;
            const actions = row.querySelector('.person-actions');
            if (p.state === 'none') {
                actions.append(button('+ Add friend', 'primary', userUrl(urls.add, p.id)));
            } else if (p.state === 'received') {
                actions.append(button('Accept', 'primary', userUrl(urls.accept, p.id)),
                               button('Decline', 'ghost', userUrl(urls.remove, p.id)));
            } else if (p.state === 'sent') {
                actions.append(tag('Requested'), button('Cancel', 'ghost', userUrl(urls.remove, p.id)));
            } else if (p.state === 'friends') {
                actions.append(tag('✓ Friends', 'friends'));
            }
            list.append(row);
        }
        panel.hidden = people.length === 0;
    }

    let timer = null;
    let lastQuery = '';
    input.addEventListener('input', () => {
        const q = input.value.trim();
        clearTimeout(timer);
        if (q.replace(/^@/, '').length < 2) {
            lastQuery = '';
            render([]);
            return;
        }
        timer = setTimeout(async () => {
            lastQuery = q;
            try {
                const res = await fetch(`${urls.search}?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                if (q === lastQuery) render(data.results);   // ignore stale responses
            } catch (err) {
                render([]);
            }
        }, 200);
    });

    // Restore the query after a friend button reloads the page (?q=...).
    // Done last so both the activity filter and the people search react to it.
    const initial = new URLSearchParams(location.search).get('q');
    if (initial) {
        input.value = initial;
        input.dispatchEvent(new Event('input'));
    }
});
