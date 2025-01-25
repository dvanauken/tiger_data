// script.js

// Set the dimensions based on the window size
const width = window.innerWidth;
const height = window.innerHeight;

// Create the SVG element within the #map div
const svg = d3.select("#map")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("version", "1.1")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("xmlns:xlink", "http://www.w3.org/1999/xlink");

// Select the progress overlay and progress bar elements
const progressOverlay = d3.select("#progress-overlay");
const progressBar = d3.select("#progress-bar");

// Function to show the progress overlay
function showProgress() {
    progressOverlay.classed("hidden", false);
    progressBar.property("value", 0);
}

// Function to update the progress bar
function updateProgress(percentage) {
    progressBar.property("value", percentage);
}

// Function to hide the progress overlay
function hideProgress() {
    progressOverlay.classed("hidden", true);
}

// Function to handle file drop
async function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    
    // Ensure the file is a TopoJSON file
    if (!file.name.endsWith('.topojson')) {
        alert("Please drop a valid .topojson file.");
        return;
    }

    showProgress(); // Show progress overlay

    const reader = new FileReader();

    // Listen to the progress event
    reader.onprogress = function(e) {
        if (e.lengthComputable) {
            const percentLoaded = Math.round((e.loaded / e.total) * 50);
            updateProgress(percentLoaded);
        }
    };

    reader.onloadstart = function() {
        updateProgress(0);
    };

    reader.onloadend = function() {
        updateProgress(50);
    };

    reader.onerror = function() {
        console.error("Error reading file.");
        alert("An error occurred while reading the file.");
        hideProgress();
    };

    reader.onload = async function(e) {
        try {
            const topology = JSON.parse(e.target.result);
            const objectName = Object.keys(topology.objects)[0];
            const features = topojson.feature(topology, topology.objects[objectName]);

            // Update progress to 60%
            updateProgress(60);
            await new Promise(resolve => setTimeout(resolve, 100));

            // Define the projection
            const projection = d3.geoMercator()
                .fitSize([width, height], features);

            // Define the path generator
            const path = d3.geoPath()
                .projection(projection);

            // Update progress to 70%
            updateProgress(70);
            await new Promise(resolve => setTimeout(resolve, 100));

            // Clear any existing content
            svg.selectAll("*").remove();

            // Bind data and create one path per feature
            svg.selectAll("path")
                .data(features.features)
                .join("path")
                .attr("class", "feature")
                .attr("d", path)
                .append("title")
                .text(d => {
                    const props = Object.entries(d.properties)
                        .map(([key, value]) => `${key}: ${value}`)
                        .join('\n');
                    return props;
                });

            // Update progress to 80%
            updateProgress(80);
            await new Promise(resolve => setTimeout(resolve, 100));

            // Optionally handle points if present
            svg.selectAll("circle")
                .data(features.features.filter(d => d.geometry.type === "Point" || d.geometry.type === "MultiPoint"))
                .join("circle")
                .attr("class", "feature")
                .attr("cx", d => projection(d.geometry.coordinates)[0])
                .attr("cy", d => projection(d.geometry.coordinates)[1])
                .attr("r", 4) // Adjust radius as needed
                .append("title")
                .text(d => {
                    const props = Object.entries(d.properties)
                        .map(([key, value]) => `${key}: ${value}`)
                        .join('\n');
                    return props;
                });

            // Update progress to 100%
            updateProgress(100);
            // Hide the progress overlay after a short delay to show 100%
            setTimeout(hideProgress, 500);
        } catch (error) {
            console.error("Error parsing TopoJSON:", error);
            alert("Failed to load the TopoJSON file. Please ensure it's valid.");
            hideProgress();
        }
    };

    reader.readAsText(file);
}

// Function to handle drag over event
function handleDragOver(event) {
    event.preventDefault();
    // Optional: Add visual feedback for drag over
    d3.select("#map").classed("dragging", true);
}

// Function to handle drag leave event (optional for visual feedback)
function handleDragLeave(event) {
    d3.select("#map").classed("dragging", false);
}

// Add event listeners for drag-and-drop functionality
document.body.addEventListener("dragover", handleDragOver);
document.body.addEventListener("dragleave", handleDragLeave); // Optional
document.body.addEventListener("drop", function(event) {
    handleDragLeave(event); // Remove visual feedback
    handleDrop(event);
});

// Optional: Handle window resize to make the SVG responsive
window.addEventListener("resize", () => {
    const newWidth = window.innerWidth;
    const newHeight = window.innerHeight;
    svg.attr("width", newWidth).attr("height", newHeight);
});
