// static/js/past-events-search.js
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('rest-search-form');
    const input = form.querySelector('input[name="q"]');
    const ajaxResults = document.getElementById('ajax-results');

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const query = input.value.trim();

        fetch(`/api/past-events/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                if (data.length === 0) {
                    ajaxResults.innerHTML = '<h3 class="center-text">No past events.</h3>';
                } else {
                    ajaxResults.innerHTML = data.map(event => `
                        <div class="u-align-left u-container-align-left u-container-style u-group u-palette-1-light-3 u-radius u-shape-round u-group-1">
                            <div class="u-container-layout u-container-layout-2">
                                <img src="${event.image1 ? event.image1 : '/static/images/452545.jpg'}" alt="${event.name}" class="u-border-2 u-border-palette-1-base u-image u-image-circle u-image-2">
                                <h3 class="u-align-center u-text u-text-2">${event.name}</h3>
                                <div class="u-align-center u-border-3 u-border-palette-1-base u-line u-line-horizontal u-line-1"></div>
                                <a href="/events/${event.id}/" class="u-btn u-button-style u-hover-palette-1-dark-1 u-palette-1-base u-btn-2">More info</a>
                            </div>
                        </div>
                    `).join('');
                }
            })
            .catch(() => {
                ajaxResults.innerHTML = '<h3 class="center-text">Error loading events.</h3>';
            });
    });
});