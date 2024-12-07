document.addEventListener("DOMContentLoaded", function () {
    const queryInput = document.getElementById("query-input");
    const suggestionsContainer = document.getElementById("autocomplete-suggestions");


    queryInput.addEventListener("input", async function () {
        const query = queryInput.value.trim().toLowerCase();
        suggestionsContainer.innerHTML = ""; // Clear previous suggestions

        if (query === "") {
            suggestionsContainer.classList.add("hidden");
            return;
        }

        try {
            // Send a request to the backend to get suggestions
            const response = await fetch(`http://localhost:5000/api/v5/suggestions?query=${encodeURIComponent(query)}`);
            console.log("Backend Response Status:", response.status); // Check response status
            if (response.ok) {
                const data = await response.json();
                console.log("Suggestions received from backend:", data); // Log the response data
                const suggestions = data.suggestions || [];

                // Show filtered suggestions
                if (suggestions.length > 0) {
                    suggestionsContainer.classList.remove("hidden");
                    suggestions.forEach((suggestion) => {
                        const li = document.createElement("li");
                        li.textContent = suggestion;
                        li.classList.add("hover:bg-gray-100");
                        li.addEventListener("click", () => {
                            queryInput.value = suggestion; // Set clicked suggestion as input value
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

    // Show the loader
    spinner.classList.remove("hidden");

    // Clear previous results
    resultsContainer.innerHTML = "";

    try {
        let searchUrl = 'http://localhost:5000/api/v5/search?query=' + encodeURIComponent(query);

        
        // Simulated search request (replace with API call in a real implementation)
        const results = await searchDocuments(searchUrl);

        // Hide the loader once results are fetched
        spinner.classList.add("hidden");
        // Display new results
        if (results.length > 0) {
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
            
            // Load and play the Lottie animation
            var animation = lottie.loadAnimation({
                container: document.getElementById('lottie-container'), // Container for the Lottie animation
                renderer: 'svg', // Use SVG rendering
                loop: true, // Loop the animation
                autoplay: true, // Auto-start the animation
                path: 'assets/Animation.json' // Path to your Lottie animation file (JSON format)
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




function highlightKeywords(text, keyword) {
    const regex = new RegExp(`(${keyword})`, 'gi');
    return text.replace(regex, '<span class="bg-yellow-200">$1</span>');
}

// Simulated document search function
async function searchDocuments(url) {
    try {
        const response = await fetch(url, {method: 'GET'});

        // Check if the response is successful
        if (!response.ok) {
            throw new Error("Failed to fetch search results");
        }
        
        const data = await response.json();

        // Return the results from the backend
        return data.results.map(result => ({
            title: result.title,
            snippet: result.snippet,
            file_path: result.file_path, // Include the file path for the link
            author: result.author // Include the author information
        }));
    } catch (error) {
        console.error("Error fetching search documents:", error);
        return []; // Return an empty array on error
    }
}



const clearBtn = document.querySelector('#clearBtn');
if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        // Clear the text from the input field
        const queryInput = document.getElementById("query-input");
        if (queryInput) {
            queryInput.value = '';
        }

        // Clear the content of the results container
        const resultsContainer = document.getElementById("results-container");
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
    });
}


