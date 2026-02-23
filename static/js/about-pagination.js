document.addEventListener('DOMContentLoaded', function () {
    const listContainer = document.getElementById('profiles-list');
    const paginationContainer = document.getElementById('profiles-pagination');

    if (!listContainer || !paginationContainer) {
        return;
    }

    paginationContainer.addEventListener('click', function (e) {
        const target = e.target;
        if (target.tagName.toLowerCase() === 'a') {
            e.preventDefault();
            const url = target.getAttribute('href');
            fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(response => response.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const newList = doc.getElementById('profiles-list');
                    const newPagination = doc.getElementById('profiles-pagination');
                    if (newList && newPagination) {
                        listContainer.innerHTML = newList.innerHTML;
                        paginationContainer.innerHTML = newPagination.innerHTML;
                        window.history.pushState({}, '', url);
                    }
                })
                .catch(err => console.error('Pagination error', err));
        }
    });
});