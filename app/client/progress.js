const Progress = (function() {
  function showProgress(loaded, total) {
      let progress = d3.select("#progress-container");
      
      if (progress.empty()) {
          progress = d3.select("body")
              .append("div")
              .attr("id", "progress-container")
              .style("position", "fixed")
              .style("top", "50%")
              .style("left", "50%")
              .style("transform", "translate(-50%, -50%)")
              .style("background", "white")
              .style("padding", "20px")
              .style("border-radius", "8px")
              .style("box-shadow", "0 2px 10px rgba(0,0,0,0.2)")
              .style("z-index", "1000");

          progress.append("div")
              .attr("id", "progress-text");
          
          progress.append("div")
              .attr("id", "progress-bar")
              .style("width", "300px")
              .style("height", "20px")
              .style("background", "#eee")
              .style("border-radius", "10px")
              .style("overflow", "hidden")
              .append("div")
              .attr("id", "progress-fill")
              .style("width", "0%")
              .style("height", "100%")
              .style("background", "#4CAF50")
              .style("transition", "width 0.3s ease");
      }

      const percent = Math.round((loaded / total) * 100);
      const mbLoaded = (loaded / 1048576).toFixed(1);
      const mbTotal = (total / 1048576).toFixed(1);

      d3.select("#progress-text")
          .text(`Loading: ${mbLoaded}MB / ${mbTotal}MB (${percent}%)`);
      
      d3.select("#progress-fill")
          .style("width", `${percent}%`);
  }

  function hideProgress() {
      d3.select("#progress-container").remove();
  }

  async function readFileWithProgress(file) {
      return new Promise((resolve, reject) => {
          const chunkSize = 1024 * 1024; // 1MB chunks
          let loaded = 0;
          const fileSize = file.size;
          let result = '';
          
          const reader = new FileReader();
          
          function readNextChunk(start) {
              const end = Math.min(start + chunkSize, fileSize);
              const slice = file.slice(start, end);
              reader.readAsText(slice);
          }

          reader.onload = (e) => {
              result += e.target.result;
              loaded += e.target.result.length;
              
              showProgress(loaded, fileSize);

              if (loaded < fileSize) {
                  readNextChunk(loaded);
              } else {
                  hideProgress();
                  resolve(result);
              }
          };

          reader.onerror = reject;
          readNextChunk(0);
      });
  }

  return {
      readFileWithProgress
  };
})();