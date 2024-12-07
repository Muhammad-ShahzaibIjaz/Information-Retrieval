let selectedFilter = 'default';
let storedQuery;

document.addEventListener("DOMContentLoaded", async function () {
    const queryInput = document.getElementById("query-input");
    const suggestionsContainer = document.getElementById("autocomplete-suggestions");
    const filterButton = document.getElementById('filter-button');
    const filterOptions = document.getElementById('filter-options');

    // Toggle filter options dropdown
    filterButton.addEventListener('click', () => {
        filterOptions.classList.toggle('hidden');
    });

    // Handle filter selection
    filterOptions.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI') {
            selectedFilter = e.target.dataset.value;
            filterOptions.classList.add('hidden');
        }
    });

    // Handle query input and fetch suggestions from backend
    queryInput.addEventListener("input", async function () {
        const query = queryInput.value.trim().toLowerCase();
        suggestionsContainer.innerHTML = ""; // Clear previous suggestions

        if (query === "") {
            suggestionsContainer.classList.add("hidden");
            return;
        }

        try {
            const response = await fetch(`http://localhost:5000/api/suggestions?query=${encodeURIComponent(query)}`);
            console.log("Backend Response Status:", response.status);
            if (response.ok) {
                const data = await response.json();
                console.log("Suggestions received from backend:", data);
                const suggestions = data.suggestions || [];

                if (suggestions.length > 0) {
                    suggestionsContainer.classList.remove("hidden");
                    suggestions.forEach((suggestion) => {
                        const li = document.createElement("li");
                        li.textContent = suggestion;
                        li.classList.add("hover:bg-gray-100");
                        li.addEventListener("click", () => {
                            queryInput.value = suggestion;
                            suggestionsContainer.classList.add("hidden");
                        });
                        suggestionsContainer.appendChild(li);
                    });
                } else {
                    suggestionsContainer.classList.add("hidden");
                }
            } else {
                console.error("Failed to fetch suggestions, status:", response.status);
                suggestionsContainer.classList.add("hidden");
            }
        } catch (error) {
            console.error("Error fetching suggestions:", error);
            suggestionsContainer.classList.add("hidden");
        }
    });

    // Hide suggestions when clicking outside
    document.addEventListener("click", (e) => {
        if (!queryInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.classList.add("hidden");
        }
        if (!filterOptions.contains(e.target) && !filterButton.contains(e.target)) {
            filterOptions.classList.add('hidden');
        }
    });
});


document.getElementById("search-form").addEventListener("submit", async function (event) {
    event.preventDefault();

    const query = document.getElementById("query-input").value.trim();
    const resultsContainer = document.getElementById("results-container");
    const spinner = document.getElementById("spinner");

    if (!query) {
        alert("Please enter a search query.");
        return;
    }

    spinner.classList.remove("hidden"); // Show loader
    resultsContainer.innerHTML = ""; // Clear previous results

    try {
        let searchUrl = 'http://localhost:5000/api/v3/search/content?query=' + encodeURIComponent(query);

        if (selectedFilter === 'title') {
            searchUrl = `http://localhost:5000/api/v3/search/title?query=${encodeURIComponent(query)}`;
        }

        const results = await searchDocuments(searchUrl);

        spinner.classList.add("hidden"); // Hide loader once results are fetched

        if (results.length > 0) {
            storedQuery = query;
            results.forEach((result, index) => {
                const highlightTitle = highlightKeywords(result.title, query);
                const highlightSnippet = highlightKeywords(result.snippet, query);
                const highlightAuthor = highlightKeywords(result.author, query);
                const resultCard = document.createElement("div");
                resultCard.className = "bg-white p-6 rounded-lg shadow-md hover:bg-gray-100";

                resultCard.innerHTML = `
                    <h3 class="text-lg font-semibold">
                        ${index + 1}. <a href="${result.file_path}" target="_blank" class="text-black docPreview">${highlightTitle}</a>
                    </h3>
                    <p class="text-gray-500 mt-2"><span class="text-[rgba(0,0,0,0.8)]">Author:</span> ${highlightAuthor}</p>
                    <p class="text-gray-600 mt-2">${highlightSnippet}</p>
                    <div class="mt-4 flex space-x-4 items-center">
                        <p class="text-[15px]">Is this document relevant to your query?</p>
                        <button class="feedback-btn relevant like-btn text-green-500 hover:text-green-700" data-doc-id="${result.doc_id}" aria-label="Like">
                            <i class="fa-solid fa-thumbs-up"></i>
                        </button>
                        <button class="feedback-btn dislike-btn text-red-500 hover:text-red-700" data-doc-id="${result.doc_id}" aria-label="Dislike">
                            <i class="fa-solid fa-thumbs-down"></i>
                        </button>
                    </div>
                `;
                resultsContainer.appendChild(resultCard);
            });
        } else {
            resultsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center text-center">
                    <div id="lottie-container" class="w-72 mb-4"></div>
                    <p class="text-[rgba(255,255,255,0.8)]">No results found for "${query}".</p>
                </div>
            `;
            var animation = lottie.loadAnimation({
                container: document.getElementById('lottie-container'),
                renderer: 'svg',
                loop: true,
                autoplay: true,
                path: 'assets/Animation.json'
            });
        }

    } catch (error) {
        spinner.classList.add("hidden"); // Hide loader in case of an error
        console.error("Error fetching results:", error);
        resultsContainer.innerHTML = `
            <p class="text-red-500">An error occurred. Please try again later.</p>
        `;
    }
});

// Event delegation for feedback button click (since buttons are dynamically added)
document.getElementById("results-container").addEventListener('click', function (e) {
    
    // Check if the clicked element has the feedback-btn class or the fa-solid class (icon)
    if (e.target && (e.target.classList.contains('feedback-btn') || e.target.closest('.feedback-btn'))) {
        e.preventDefault();
        e.stopPropagation();
        
        // Get the button element (if clicked on icon, get the parent button)
        const feedbackBtn = e.target.closest('.feedback-btn');

        // Get the document ID and relevance from the button (not the icon)
        const docId = feedbackBtn.dataset.docId;
        const relevance = feedbackBtn.classList.contains('relevant') ? 'relevant' : 'not-relevant';

        storeFeedback(docId, relevance);
    }
});

// Function to send feedback to the backend
async function sendFeedback(docId, relevance) {
    try {
        const response = await fetch('http://localhost:5000/api/v3/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                doc_id: docId,
                keyword: storedQuery,
                relevance: relevance
            })
        });

        if (response.ok) {
            console.log('Feedback sent successfully');
        } else {
            console.error('Error sending feedback:', response.status);
        }
    } catch (error) {
        console.error('Error sending feedback:', error);
    }
}

// Store feedback in local storage or memory (example using localStorage)
function storeFeedback(docId, relevance) {
    let feedback = JSON.parse(localStorage.getItem('feedback')) || [];
    feedback.push({ docId, relevance, timestamp: new Date() });
    localStorage.setItem('feedback', JSON.stringify(feedback));
}

// Periodically send feedback data
function sendFeedbackPeriodically() {
    setInterval(() => {
        const feedback = JSON.parse(localStorage.getItem('feedback')) || [];
        console.log(feedback);
        if (feedback.length > 0) {
            // Send feedback to the backend
            feedback.forEach(async (item) => {
                await sendFeedback(item.docId, item.relevance);
            });

            // Clear feedback after sending to the backend
            localStorage.removeItem('feedback');
        }
    }, 10000); // Send feedback every 60 seconds (adjust interval as needed)
}


document.addEventListener('visibilitychange', function() {
    if (document.hidden) {
        // The page is being hidden (e.g., tab is closing or switching)
        console.log("The tab is being closed or switched.");
        const feedback = JSON.parse(localStorage.getItem('feedback')) || [];
        console.log(feedback);
        if (feedback.length > 0) {
            // Send feedback to the backend
            feedback.forEach(async (item) => {
                await sendFeedback(item.docId, item.relevance);
            });

            // Clear feedback after sending to the backend
            localStorage.removeItem('feedback');
        }
    } else {
        // The page is visible again (e.g., tab is brought back into view)
        console.log("The tab is now active.");
    }
});


// sendFeedbackPeriodically();


function highlightKeywords(text, keyword) {
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.replace(regex, '<span class="bg-yellow-200">$1</span>');
}


// Simulated document search function
async function searchDocuments(url) {
    try {
        const response = await fetch(url, {method: 'GET'});

        if (!response.ok) {
            throw new Error("Failed to fetch search results");
        }
        
        const data = await response.json();
        return data.results.map(result => ({
            doc_id: result.doc_id,
            title: result.title,
            snippet: result.snippet,
            file_path: result.file_path,
            author: result.author
        }));
    } catch (error) {
        console.error("Error fetching search documents:", error);
        return [];
    }
}

const clearBtn = document.querySelector('#clearBtn');
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        const queryInput = document.getElementById("query-input");
        if (queryInput) queryInput.value = '';
        const resultsContainer = document.getElementById("results-container");
        if (resultsContainer) resultsContainer.innerHTML = '';
    });
}
