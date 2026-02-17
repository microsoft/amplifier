document.addEventListener('DOMContentLoaded', () => {
    const movies = [
        { id: 'the-brutalist', title: 'The Brutalist', category: 'Best Picture' },
        { id: 'anora', title: 'Anora', category: 'Best Picture' },
        { id: 'conclave', title: 'Conclave', category: 'Best Picture' },
        { id: 'emilia-perez', title: 'Emilia Pérez', category: 'Best Picture' },
        { id: 'wicked', title: 'Wicked', category: 'Best Picture' },
        { id: 'brady-corbet', title: 'Brady Corbet', category: 'Best Director' },
        { id: 'sean-baker', title: 'Sean Baker', category: 'Best Director' },
        { id: 'james-mangold', title: 'James Mangold', category: 'Best Director' },
        { id: 'adrien-brody', title: 'Adrien Brody', category: 'Best Actor' },
        { id: 'timothee-chalamet', title: 'Timothée Chalamet', category: 'Best Actor' },
    ];

    const movieCardsContainer = document.getElementById('movie-cards-container');
    const resultsContainer = document.getElementById('results-container');

    // Initialize votes from localStorage (with fallback if corrupted/disabled)
    let votes = {};
    let votedCategories = {};
    try {
        votes = JSON.parse(localStorage.getItem('oscarsVotes')) || {};
        votedCategories = JSON.parse(localStorage.getItem('oscarsVotedCategories')) || {};
    } catch (e) {
        votes = {};
        votedCategories = {};
    }

    // Function to render movie cards
    function renderMovieCards() {
        movieCardsContainer.innerHTML = ''; // Clear existing cards
        movies.forEach(movie => {
            const movieCard = document.createElement('div');
            movieCard.className = 'movie-card';
            movieCard.innerHTML = `
                <h3>${movie.title}</h3>
                <p>Category: ${movie.category}</p>
                <button class="vote-button" data-movie-id="${movie.id}" data-category="${movie.category}">Vote</button>
                <p class="vote-count" data-vote-count="${movie.id}">Votes: ${votes[movie.id] || 0}</p>
                <p class="vote-message" data-vote-message="${movie.id}" style="display: none;"></p>
            `;
            movieCardsContainer.appendChild(movieCard);
        });
        addEventListenersToVoteButtons();
        updateVoteCounts();
    }

    // Function to add event listeners to vote buttons
    function addEventListenersToVoteButtons() {
        document.querySelectorAll('.vote-button').forEach(button => {
            button.addEventListener('click', (event) => {
                const movieId = event.target.dataset.movieId;
                const category = event.target.dataset.category;
                const card = event.target.closest('.movie-card');
                const voteMessageElement = card.querySelector(`[data-vote-message="${movieId}"]`);

                if (votedCategories[category]) {
                    voteMessageElement.textContent = 'You already voted in this category!';
                    voteMessageElement.style.display = 'block';
                    setTimeout(() => voteMessageElement.style.display = 'none', 3000);
                    return;
                }

                votes[movieId] = (votes[movieId] || 0) + 1;
                votedCategories[category] = true;
                try {
                    localStorage.setItem('oscarsVotes', JSON.stringify(votes));
                    localStorage.setItem('oscarsVotedCategories', JSON.stringify(votedCategories));
                } catch (e) {
                    // localStorage unavailable — votes still work in-memory for this session
                }
                updateVoteCounts();
                renderResults();
                disableCategoryButtons(category);
            });
            // Disable buttons if already voted in the category
            if (votedCategories[button.dataset.category]) {
                button.disabled = true;
            }
        });
    }

    // Function to disable buttons for a category after voting
    function disableCategoryButtons(category) {
        document.querySelectorAll(`.vote-button[data-category="${category}"]`).forEach(button => {
            button.disabled = true;
        });
    }

    // Function to update vote counts displayed on cards
    function updateVoteCounts() {
        movies.forEach(movie => {
            const voteCountElement = document.querySelector(`[data-vote-count="${movie.id}"]`);
            if (voteCountElement) {
                voteCountElement.textContent = `Votes: ${votes[movie.id] || 0}`;
            }
        });
    }

    // Function to render live results
    function renderResults() {
        resultsContainer.innerHTML = '';
        const allCategories = [...new Set(movies.map(movie => movie.category))];

        allCategories.forEach(category => {
            const categoryResults = document.createElement('div');
            categoryResults.innerHTML = `<h3>${category}</h3>`;

            const moviesInCategory = movies.filter(movie => movie.category === category);
            moviesInCategory.sort((a, b) => (votes[b.id] || 0) - (votes[a.id] || 0)); // Sort by votes descending

            moviesInCategory.forEach(movie => {
                const resultItem = document.createElement('div');
                resultItem.innerHTML = `
                    <span>${movie.title}</span>
                    <span>${votes[movie.id] || 0}</span>
                `;
                categoryResults.appendChild(resultItem);
            });
            resultsContainer.appendChild(categoryResults);
        });

        if (Object.keys(votes).length === 0) {
            resultsContainer.innerHTML = '<p>No votes yet. Be the first to vote!</p>';
        }
    }

    // Initial rendering
    renderMovieCards();
    renderResults();
});
