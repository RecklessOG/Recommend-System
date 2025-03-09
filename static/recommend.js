$(function () {
    $("#autoComplete").on("input", function () {
        $(".movie-button").attr("disabled", $(this).val().trim() === "");
    });

    $(".movie-button").on("click", function () {
        var my_api_key = "64e7a74b2de23c092d569c61618303f9";
        var title = $("#autoComplete").val().trim();

        if (title === "") {
            $(".results").hide();
            $(".fail").show();
        } else {
            $("#loader").fadeIn();
            load_details(my_api_key, title);
        }
    });
});

function load_details(my_api_key, title) {
    $.ajax({
        type: "GET",
        url: `https://api.themoviedb.org/3/search/movie?api_key=${my_api_key}&query=${title}`,
        success: function (movie) {
            if (movie.results.length < 1) {
    $(".fail").show();
    $(".results").hide();
    $("#recommendations").empty(); // Clear previous recommendations
    $("#loader").fadeOut();
    return;
}
 else {
                $(".fail").hide();
                var movie_id = movie.results[0].id;
                var movie_title = movie.results[0].original_title;
                get_movie_details(movie_id, my_api_key, movie_title);
            }
        },
        error: function () {
            alert("Invalid Request");
            $("#loader").fadeOut();
        }
    });
}

function get_movie_details(movie_id, my_api_key, movie_title) {
    $.ajax({
        type: "GET",
        url: `https://api.themoviedb.org/3/movie/${movie_id}?api_key=${my_api_key}`,
        success: function (movie_details) {
            show_details(movie_details, movie_title);
            movie_recs(movie_title, movie_id, my_api_key);


            console.log("Fetching Cast for Movie ID:", movie_id); // Debugging log
            get_movie_cast(movie_id, my_api_key); // ✅ Ensure cast details are fetched

            console.log("Fetching Trailer for Movie ID:", movie_id); // 🔴 Add this line
            get_trailer(movie_id, my_api_key);  // ✅ Call get_trailer here
        },
        error: function () {
            alert("API Error!");
            $("#loader").fadeOut();
        }
    });
}

function get_trailer(movie_id, my_api_key) {
    console.log("Fetching trailer for movie ID:", movie_id);

    if (!movie_id || isNaN(movie_id)) {
        console.error("Invalid movie_id:", movie_id);
        return;
    }

    $.ajax({
        type: "GET",
        url: `https://api.themoviedb.org/3/movie/${movie_id}/videos?api_key=${my_api_key}`,
        success: function (response) {
            console.log("Trailer API Response:", response);

            if (response.results.length > 0) {
                var trailer = response.results.find(video => video.type === "Trailer" && video.site === "YouTube");
                if (trailer) {
                    var trailerUrl = `https://www.youtube.com/watch?v=${trailer.key}`;
                    console.log("✅ Trailer Found:", trailerUrl);

                    // Find the correct section where the trailer button already exists
                    let trailerButton = $("#trailerButton");

                    if (trailerButton.length > 0) {
                        // ✅ Show the existing button and set the correct trailer link
                        trailerButton
                            .show()
                            .off("click")
                            .on("click", function () {
                                window.open(trailerUrl, "_blank");
                            });
                    } else {
                        console.warn("❌ Trailer button not found in the expected location.");
                    }
                } else {
                    console.log("No YouTube trailer found.");
                    $("#trailerButton").hide();
                }
            } else {
                console.log("No videos found for this movie.");
                $("#trailerButton").hide();
            }
        },
        error: function (xhr) {
            console.error("API Error:", xhr.responseText);
            $("#trailerButton").hide();
        }
    });
}

function movie_recs(movie_title, movie_id, my_api_key) {
    $.ajax({
        type: "POST",
        url: "/similarity",
        data: { name: movie_title },
        success: function (response) {
function movie_recs(movie_title, movie_id, my_api_key) {
    $.ajax({
        type: "POST",
        url: "/similarity",
        data: { name: movie_title },
        success: function (response) {
            if (response.status === "error") {
                $(".fail").show();
                $(".results").hide();
                $("#recommendations").empty(); // Clears recommendations
                $("h3:contains('Recommendations')").remove(); // Removes the heading
                $("#loader").fadeOut();
                return;
            }
            var movie_arr = response.recommendations;
            displayRecommendations(movie_arr, my_api_key);
        },
        error: function () {
            alert("Error fetching recommendations");
            $("#loader").fadeOut();
        }
    });
}



            var movie_arr = response.recommendations;
            displayRecommendations(movie_arr, my_api_key);
        },
        error: function () {
            alert("Error fetching recommendations");
            $("#loader").fadeOut();
        }
    });
}

function displayRecommendations(recommendations, my_api_key) {
    const recommendationContainer = $("#recommendations");
    recommendationContainer.empty();

    // Add Recommendations heading BEFORE appending movies, only if it doesn't exist
    if ($("#recommendations").siblings("h3").length === 0) {
        $("#recommendations").before("<h3 class='w-100 text-center mt-4'>Recommendations</h3>");
    }

    recommendations.forEach(function (movie) {
        $.ajax({
            type: "GET",
            url: `https://api.themoviedb.org/3/search/movie?api_key=${my_api_key}&query=${movie}`,
            success: function (data) {
                if (data.results.length > 0) {
                    const movieData = data.results[0];
                    const posterPath = movieData.poster_path
                        ? `https://image.tmdb.org/t/p/w500${movieData.poster_path}`
                        : "default-image.jpg";  // Use a fallback image if unavailable

                    const movieCard = `
                        <div class="col-md-3 mb-4 text-center">
                            <div class="card">
                                <img src="${posterPath}" class="card-img-top" alt="${movieData.title} Poster">
                                <div class="card-body">
                                    <h5 class="movie-title">${movieData.title}</h5>
                                    <!-- Add to Watchlist Button -->
                                    <button class="btn btn-danger add-to-watchlist"
                                        data-movie-id="${movieData.id}"
                                        data-movie-title="${movieData.title}"
                                        data-movie-image="${posterPath}">
                                        Add to Watchlist
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                    recommendationContainer.append(movieCard);
                }
            },
            error: function () {
                console.error("Error fetching recommendation details");
            }
        });
    });

    // Handle Add to Watchlist button click
    $(document).off("click", ".add-to-watchlist").on("click", ".add-to-watchlist", function () {
    let movieId = $(this).data("movie-id");
    let movieTitle = $(this).data("movie-title");

    console.log("Movie ID:", movieId);
    console.log("Movie Title:", movieTitle);

    if (!movieId || !movieTitle) {
        alert("Invalid movie data.");
        return;
    }

    $.ajax({
        url: "/add_to_watchlist",
        type: "POST",
        data: {
            movie_id: movieId,
            movie_title: movieTitle
        },
        success: function (response) {
            alert(response.message);
        },
        error: function (xhr) {
            if (xhr.status === 401) {
                alert("Please log in to add movies to your watchlist!");
            } else if (xhr.status === 409) {
                alert("This movie is already in your watchlist!");
            } else {
                console.error("Error adding to watchlist:", xhr);
            }
        }
    });
});

    $("#loader").fadeOut();
}




function show_details(movie_details, movie_title) {
    var poster = movie_details.poster_path
        ? `https://image.tmdb.org/t/p/original${movie_details.poster_path}`
        : "https://via.placeholder.com/300x450?text=No+Image";

    var genres = movie_details.genres.length > 0 ? movie_details.genres.map(g => g.name).join(", ") : "N/A";
    var overview = movie_details.overview || "No overview available.";
    var rating = movie_details.vote_average ? movie_details.vote_average.toFixed(1) : "Not rated";
    var vote_count = movie_details.vote_count ? movie_details.vote_count.toLocaleString() : "No votes";
    var release_date = movie_details.release_date ? new Date(movie_details.release_date).toDateString().split(" ").slice(1).join(" ") : "Unknown";
    var runtime = movie_details.runtime ? `${Math.floor(movie_details.runtime / 60)}h ${movie_details.runtime % 60}m` : "N/A";
    var tagline = movie_details.tagline ? `"${movie_details.tagline}"` : "";

    $(".results").html(`
        <div class="movie-container">
            <h2>${movie_title}</h2>
            <p class="tagline">${tagline}</p>
            <div class="movie-content">
                <img src="${poster}" alt="${movie_title} Poster" class="movie-poster">
                <div class="movie-info">
                    <p><strong>Genres:</strong> ${genres}</p>
                    <p><strong>Overview:</strong> ${overview}</p>
                    <p><strong>Rating:</strong> ${rating} (${vote_count} votes)</p>
                    <p><strong>Release Date:</strong> ${release_date}</p>
                    <p><strong>Runtime:</strong> ${runtime}</p>
                </div>
            </div>
            <button class="trailer-button" onclick="watchTrailer('${movie_details.id}')">Click Here for Trailer</button>

            <!-- Star Rating System -->
            <div class="rating-container">
                <p><strong>Rate this movie:</strong></p>
                <div class="stars" data-movie-id="${movie_details.id}">
                    <span class="star" data-value="1">&#9733;</span>
                    <span class="star" data-value="2">&#9733;</span>
                    <span class="star" data-value="3">&#9733;</span>
                    <span class="star" data-value="4">&#9733;</span>
                    <span class="star" data-value="5">&#9733;</span>
                </div>
            </div>
        </div>
        <div id="cast-section" class="row mt-4"></div>
    `);

    $(".results").show();
    $("#loader").fadeOut();

    var movieId = movie_details.id;

    // Fetch and highlight previous rating
    $.ajax({
        url: "/get_rating",
        type: "GET",
        data: { movie_id: movieId },
        xhrFields: { withCredentials: true },
        success: function (response) {
            if (response.rating) {
                $(".stars .star").each(function () {
                    var starValue = $(this).data("value");
                    $(this).toggleClass("selected", starValue <= response.rating);
                });
            }
        },
        error: function (xhr, status, error) {
            console.error("Error fetching rating:", error);
        }
    });

    // Star rating click event
   $(".stars .star").on("click", function () {
    var selectedRating = $(this).data("value");
    var movieId = $(this).closest(".stars").data("movie-id"); // Ensure correct movieId

    // Send rating to backend first
    $.ajax({
        url: "/submit_rating",
        type: "POST",
        contentType: "application/json",
        xhrFields: { withCredentials: true }, // Ensure cookies are sent
        data: JSON.stringify({ movie_id: movieId, rating: selectedRating }),
        success: function (response) {
            if (response.alert) {
                alert(response.alert); // Show alert if user is not logged in
            } else {
                console.log("Rating submitted successfully:", response);

                // ✅ Highlight stars ONLY if the rating is successfully stored
                $(".stars[data-movie-id='" + movieId + "'] .star").each(function () {
                    $(this).toggleClass("selected", $(this).data("value") <= selectedRating);
                });
            }
        },
        error: function (xhr, status, error) {
            console.error("Error submitting rating:", error);
        }
    });
});
}

// Fetch Cast Details
function get_movie_cast(movie_id, my_api_key) {
    $.ajax({
        type: "GET",
        url: `https://api.themoviedb.org/3/movie/${movie_id}/credits?api_key=${my_api_key}`,
        success: function (credits) {
            if (credits.cast.length > 0) {
                displayCastDetails(credits.cast.slice(0, 10)); // Get top 10 cast members
            } else {
                $("#cast-section").html("<p class='text-center w-100'>No cast information available.</p>");
            }
        },
        error: function () {
            console.error("Error fetching cast details");
        }
    });
}

// Display Cast Information
function displayCastDetails(cast) {
    const castContainer = $("#cast-section");
    castContainer.empty(); // Clear previous cast data

    castContainer.append("<h3 class='w-100 text-center mb-3'>Top Cast</h3>"); // Title for Cast Section

    cast.forEach(function (actor) {
        const actorImage = actor.profile_path
            ? `https://image.tmdb.org/t/p/w500${actor.profile_path}`
            : 'https://via.placeholder.com/150x225?text=No+Image';

        // Adding "Click Me" button under actor image
        const castCard = `
            <div class="col-md-2 mb-4 text-center">
                <div class="card">
                    <img src="${actorImage}" class="card-img-top" alt="${actor.name}">
                    <div class="card-body">
                        <h6 class="actor-name"><strong>${actor.name}</strong></h6>
                        <p class="character-name">as ${actor.character || "Unknown"}</p>
                        <button class="btn btn-primary actor-btn" data-actor-id="${actor.id}">Click Me</button>
                    </div>
                </div>
            </div>
        `;
        castContainer.append(castCard);
    });

    $("#loader").fadeOut();
}
// Ensure existing cast fetching remains
$(document).on("click", ".actor-btn", function () {
    let actorId = $(this).data("actor-id");
    console.log("Button clicked! Actor ID:", actorId); // Debug log
    if (actorId) {
        get_actor_details(actorId);
    } else {
        console.error("Actor ID is undefined!");
    }
});


// Fetch actor details and show popup
function get_actor_details(actor_id) {
    const my_api_key = "64e7a74b2de23c092d569c61618303f9";

    $.ajax({
        type: "GET",
        url: `https://api.themoviedb.org/3/person/${actor_id}?api_key=${my_api_key}`,
        success: function (actor) {
    console.log("Actor Details:", actor); // Debugging Log

    const imageSrc = actor.profile_path
        ? `https://image.tmdb.org/t/p/w500${actor.profile_path}`
        : "https://via.placeholder.com/200x300?text=No+Image";

    // ✅ Update the existing modal with full actor details
    $("#actorModalContent").html(`
        <div style="text-align: center;">
            <img src="${imageSrc}" alt="${actor.name}" style="width: 150px; height: 225px; border-radius: 10px;">
            <h2>${actor.name}</h2>
            <p><strong>Born:</strong> ${actor.birthday || 'N/A'}</p>
            <p><strong>Place of Birth:</strong> ${actor.place_of_birth || 'N/A'}</p>
            <p><strong>Biography:</strong> ${actor.biography ? actor.biography.substring(0, 500) + "..." : "No biography available."}</p>
            <button id="closeModal" style="margin-top: 10px;">Close</button>
        </div>
    `);

    // ✅ Show the modal
    $("#actorModal").fadeIn();
},

        error: function () {
            alert("Error fetching actor details");
        }
    });
}



// Close modal when clicking "X"
$(document).on("click", "#closeModal", function () {
    $("#actorModal").fadeOut();
});

$(window).on("click", function (event) {
    if ($(event.target).is("#actorModal")) {
        $("#actorModal").fadeOut();
    }
});

function watchTrailer(movieId) {
    if (!movieId) {
        alert("No movie ID available for the trailer.");
        return;
    }

    // Redirect to trailer page
    window.location.href = `/trailer/${movieId}`;
}

function removeFromWatchlist(movieId) {
    if (!movieId) {
        alert("Invalid movie ID.");
        return;
    }

    fetch('/remove_from_watchlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Movie removed successfully!");

            // Select row by data attribute instead of ID
            let row = document.querySelector(`tr[data-movie-id="${movieId}"]`);
            if (row) {
                console.log("Removing row:", row);
                row.remove();
            } else {
                console.log("Row not found for movie ID:", movieId);
            }
        } else {
            alert("Failed to remove movie: " + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

