// Floating Review Widget
window.addEventListener("DOMContentLoaded", () => {
    const reviewWidget = document.createElement("div");
    reviewWidget.id = "review-widget";
    reviewWidget.innerHTML = `
        <div id="review-button">💬 Reviews</div>
        <div id="review-box" class="hidden">
            <div id="review-header">
                <span>Reviews</span>
                <button id="close-review">&times;</button>
            </div>
            <div id="review-content"></div>
            <textarea id="review-input" placeholder="Write your review..."></textarea>
            <button id="submit-review">Submit</button>
        </div>
    `;

    // Append to the main container where the footer was
    const mainContainer = document.querySelector(".container");
    if (mainContainer) {
        mainContainer.appendChild(reviewWidget);
    }

    const reviewButton = document.getElementById("review-button");
    const reviewBox = document.getElementById("review-box");
    const closeReview = document.getElementById("close-review");
    const submitReview = document.getElementById("submit-review");
    const reviewInput = document.getElementById("review-input");
    const reviewContent = document.getElementById("review-content");

    // Toggle review box
    reviewButton.addEventListener("click", () => reviewBox.classList.toggle("hidden"));
    closeReview.addEventListener("click", () => reviewBox.classList.add("hidden"));

    // Submit review
    submitReview.addEventListener("click", async () => {
        const reviewText = reviewInput.value.trim();
        if (!reviewText) return;

        // Send review to backend (adjust URL as needed)
        const response = await fetch("/submit_review", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ review: reviewText })
        });
        if (response.ok) {
            reviewContent.innerHTML += `<p>${reviewText}</p>`;
            reviewInput.value = "";
        }
    });
});

// Styles for the review widget
document.head.insertAdjacentHTML("beforeend", `
    <style>
        #review-widget {
            position: fixed;
            bottom: 20px;
            right: 20px;
            font-family: Arial, sans-serif;
            z-index: 1000;
        }
        #review-button {
            background: rgba(255, 255, 255, 0.1);
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            cursor: pointer;
            backdrop-filter: blur(10px);
            transition: 0.3s;
        }
        #review-button:hover { background: rgba(255, 255, 255, 0.2); }
        #review-box {
            background: rgba(0, 0, 0, 0.8);
            color: white;
            width: 250px;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.5);
            backdrop-filter: blur(10px);
            display: flex;
            flex-direction: column;
            gap: 10px;
            position: fixed;
            bottom: 50px;
            right: 20px;
        }
        .hidden { display: none; }
        #review-header { display: flex; justify-content: space-between; align-items: center; }
        #close-review { background: none; border: none; color: white; font-size: 18px; cursor: pointer; }
        #review-input { width: 100%; padding: 5px; }
        #submit-review {
            background: #ff4757;
            color: white;
            border: none;
            padding: 5px;
            cursor: pointer;
            border-radius: 5px;
        }
        #submit-review:hover { background: #ff6b81; }
    </style>
`);
