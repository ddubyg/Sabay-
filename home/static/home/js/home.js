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
