const width = window.innerWidth;
const height = window.innerHeight;

const svg = d3.select("#map")
    .append("svg")
    .attr("width", width)
    .attr("height", height)
    .attr("version", "1.1")
    .attr("xmlns", "http://www.w3.org/2000/svg")
    .attr("xmlns:xlink", "http://www.w3.org/1999/xlink");

let fileContent = '';
let topology = null;
let features = null;

function updateProgress(type, percent, text) {
    d3.select(`#${type}-progress`)
        .property("value", percent);
    d3.select(`#${type}-label`)
        .text(`${text}: ${Math.round(percent)}%`);
}

async function processJSON(content, updateCallback) {
    const chunkSize = 1024 * 1024;
    const totalChunks = Math.ceil(content.length / chunkSize);
    let processed = 0;

    for (let i = 0; i < totalChunks; i++) {
        const start = i * chunkSize;
        const end = Math.min(start + chunkSize, content.length);
        processed = (i + 1) / totalChunks * 100;
        updateCallback(processed);
        await new Promise(resolve => setTimeout(resolve, 0));
    }

    return JSON.parse(content);
}

async function handleDrop(event) {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    
    if (!file.name.endsWith('.topojson')) {
        alert("Please drop a valid .topojson file.");
        return;
    }

    d3.select("#progress-overlay").classed("hidden", false);
    updateProgress("file", 0, "File Loading");
    updateProgress("parse", 0, "Parsing TopoJSON");
    updateProgress("render", 0, "Rendering Features");

    try {
        // File Loading Phase
        const reader = new FileReader();
        reader.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                updateProgress("file", percent, "File Loading");
            }
        };

        fileContent = await new Promise((resolve, reject) => {
            reader.onload = e => resolve(e.target.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsText(file);
        });

        updateProgress("file", 100, "File Loading");

        // Parsing Phase
        topology = await processJSON(fileContent, (percent) => {
            updateProgress("parse", percent, "Parsing TopoJSON");
        });

        const objectName = Object.keys(topology.objects)[0];
        features = topojson.feature(topology, topology.objects[objectName]);

        // Rendering Phase
        const totalFeatures = features.features.length;
        let renderedFeatures = 0;

        const projection = d3.geoMercator().fitSize([width, height], features);
        const path = d3.geoPath().projection(projection);

        svg.selectAll("*").remove();

        // Render features in chunks
        const featureChunkSize = 100;
        for (let i = 0; i < features.features.length; i += featureChunkSize) {
            const chunk = features.features.slice(i, i + featureChunkSize);
            
            svg.selectAll(`path.feature-chunk-${i}`)
                .data(chunk)
                .join("path")
                .attr("class", d => `feature feature-chunk-${i}`)
                .attr("d", path)
                .append("title")
                .text(d => Object.entries(d.properties)
                    .map(([key, value]) => `${key}: ${value}`)
                    .join('\n')
                );

            renderedFeatures += chunk.length;
            const renderPercent = (renderedFeatures / totalFeatures) * 100;
            updateProgress("render", renderPercent, "Rendering Features");
            
            await new Promise(resolve => setTimeout(resolve, 0));
        }

        setTimeout(() => {
            d3.select("#progress-overlay").classed("hidden", true);
        }, 500);

    } catch (error) {
        console.error("Error:", error);
        alert("Error processing file");
        d3.select("#progress-overlay").classed("hidden", true);
    }
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
    svg.attr("width", window.innerWidth)
       .attr("height", window.innerHeight);
});