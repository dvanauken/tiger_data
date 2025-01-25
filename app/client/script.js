const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#map")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("version", "1.1")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("xmlns:xlink", "http://www.w3.org/1999/xlink");

const progressOverlay = d3.select("#progress-overlay");
const progressBar = d3.select("#progress-bar");

function showProgress() {
    progressOverlay.classed("hidden", false);
    progressBar.property("value", 0);
}

function updateProgress(percentage) {
    progressBar.property("value", percentage);
}

function hideProgress() {
    progressOverlay.classed("hidden", true);
}

async function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    
    if (!file.name.endsWith('.topojson')) {
        alert("Please drop a valid .topojson file.");
        return;
    }

    showProgress();

    const fileSize = file.size;
    const chunkSize = 512 * 1024;
    let totalProcessingTime = fileSize; // Initialize with file size
    let currentProgress = 0;
    let offset = 0;
    let fileContent = '';
    
    const startTime = performance.now();

    const readChunk = () => {
        const chunk = file.slice(offset, offset + chunkSize);
        const chunkReader = new FileReader();
        
        chunkReader.onload = async (e) => {
            fileContent += e.target.result;
            offset += e.target.result.length;
            
            // Update progress based on bytes read
            currentProgress = (offset / fileSize) * 100;
            updateProgress(currentProgress);
            
            if (offset < fileSize) {
                readChunk();
            } else {
                try {
                    const parseStart = performance.now();
                    const topology = JSON.parse(fileContent);
                    const parseTime = performance.now() - parseStart;
                    
                    const objectName = Object.keys(topology.objects)[0];
                    const features = topojson.feature(topology, topology.objects[objectName]);
                    
                    const renderStart = performance.now();
                    const projection = d3.geoMercator()
                        .fitSize([width, height], features);

                    const path = d3.geoPath()
                        .projection(projection);

                    svg.selectAll("*").remove();

                    // Render paths
                    const pathFeatures = features.features.filter(d => 
                        d.geometry.type !== "Point" && d.geometry.type !== "MultiPoint"
                    );
                    
                    let featuresProcessed = 0;
                    const totalFeatures = pathFeatures.length;

                    svg.selectAll("path")
                        .data(pathFeatures)
                        .join("path")
                        .attr("class", "feature")
                        .attr("d", path)
                        .append("title")
                        .text(d => {
                            featuresProcessed++;
                            const renderProgress = (featuresProcessed / totalFeatures) * 20;
                            updateProgress(80 + renderProgress);
                            return Object.entries(d.properties)
                                .map(([key, value]) => `${key}: ${value}`)
                                .join('\n');
                        });

                    // Render points
                    const pointFeatures = features.features.filter(d => 
                        d.geometry.type === "Point" || d.geometry.type === "MultiPoint"
                    );

                    svg.selectAll("circle")
                        .data(pointFeatures)
                        .join("circle")
                        .attr("class", "feature")
                        .attr("cx", d => projection(d.geometry.coordinates)[0])
                        .attr("cy", d => projection(d.geometry.coordinates)[1])
                        .attr("r", 4)
                        .append("title")
                        .text(d => Object.entries(d.properties)
                            .map(([key, value]) => `${key}: ${value}`)
                            .join('\n')
                        );

                    const totalTime = performance.now() - startTime;
                    console.log(`File size: ${fileSize} bytes`);
                    console.log(`Parse time: ${parseTime}ms`);
                    console.log(`Total processing time: ${totalTime}ms`);

                    setTimeout(hideProgress, 500);
                } catch (error) {
                    console.error("Error parsing TopoJSON:", error);
                    alert("Failed to load the TopoJSON file. Please ensure it's valid.");
                    hideProgress();
                }
            }
        };
        
        chunkReader.onerror = function() {
            console.error("Error reading chunk");
            alert("An error occurred while reading the file.");
            hideProgress();
        };
        
        chunkReader.readAsText(chunk);
    };
    
    updateProgress(0);
    readChunk();
}

function handleDragOver(event) {
    event.preventDefault();
    d3.select("#map").classed("dragging", true);
}

function handleDragLeave(event) {
    d3.select("#map").classed("dragging", false);
}

document.body.addEventListener("dragover", handleDragOver);
document.body.addEventListener("dragleave", handleDragLeave);
document.body.addEventListener("drop", function(event) {
    handleDragLeave(event);
    handleDrop(event);
});

window.addEventListener("resize", () => {
    const newWidth = window.innerWidth;
    const newHeight = window.innerHeight;
    svg.attr("width", newWidth).attr("height", newHeight);
});