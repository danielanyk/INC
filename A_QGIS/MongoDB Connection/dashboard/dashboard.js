try {
    // UPDATING ALL THE GRAPHS MAIN RUN FUNCTION

    // Debugging functions
    function print(message) {
        var formattedMessage;

        if (Array.isArray(message)) {
            formattedMessage = JSON.stringify(message, null, 2);
        } else if (typeof message === 'object') {
            formattedMessage = JSON.stringify(message, null, 2);
        } else if (typeof message === 'string') {
            formattedMessage = `"${message}"`; // Add quotes around strings
        } else {
            formattedMessage = message; // Numbers and other types remain unchanged
        }

        var errorMessage = "HELLO" + formattedMessage
        var errorContainer = document.getElementById("testing");
        errorContainer.innerHTML += errorMessage;
        errorContainer.innerHTML += "<br>";
    }

    // Function to add tags
    function addTag(tag, setList, container) {
        setList.push(tag);

        const div = document.createElement('div');
        div.classList.add('tag');
        div.textContent = tag;

        // Adding button to remove tag
        const button = document.createElement('button');
        button.textContent = 'x';
        button.classList.add('tag-close');

        //when button is pressed, run removeTag function
        button.addEventListener('click', () => {
            const index = setList.indexOf(tag);
            if (index > -1) {
                setList.splice(index, 1);
                updateGraphsOnly();
                container.removeChild(div);
            }
        })
        div.appendChild(button);
        container.appendChild(div);
    }

    function updateGraph(setChange = False) {

        if ((!tSet.includes(document.getElementById('town-select').value)) && (document.getElementById('town-select').value) != "Nil") {
            if (setChange == "t") {
                addTag(document.getElementById('town-select').value, tSet, document.getElementById('town-tags'))
            }
        }

        if ((!dSet.includes(document.getElementById('day-select').value)) && (document.getElementById('day-select').value) != "Nil") {
            if (setChange == "d") {
                addTag(document.getElementById('day-select').value, dSet, document.getElementById('day-tags'))
            }
        }

        if ((!mSet.includes(document.getElementById('month-select').value)) && (document.getElementById('month-select').value) != "Nil") {
            if (setChange == "m") {
                addTag(document.getElementById('month-select').value, mSet, document.getElementById('month-tags'))
            }
        }

        if ((!ySet.includes(document.getElementById('year-select').value)) && (document.getElementById('year-select').value) != "Nil") {
            if (setChange == "y") {
                addTag(document.getElementById('year-select').value, ySet, document.getElementById('year-tags'))
            }
        }

        if ((!bSet.includes(document.getElementById('batch-select').value)) && (document.getElementById('batch-select').value) != "Nil") {
            if (setChange == "b") {
                addTag(document.getElementById('batch-select').value, bSet, document.getElementById('batch-tags'))
            }
        }

        if ((!defectSet.includes(document.getElementById('defect-select').value)) && (document.getElementById('defect-select').value) != "Nil") {
            if (setChange == "defect") {
                addTag(document.getElementById('defect-select').value, defectSet, document.getElementById('defect-tags'))
            }
        }

        if ((!typeSet.includes(document.getElementById('type-select').value)) && (document.getElementById('type-select').value) != "Nil") {
            if (setChange == "type") {
                addTag(document.getElementById('type-select').value, typeSet, document.getElementById('type-tags'))
            }
        }

        if ((!severitySet.includes(document.getElementById('severity-select').value)) && (document.getElementById('severity-select').value) != "Nil") {
            if (setChange == "severity") {
                addTag(document.getElementById('severity-select').value, severitySet, document.getElementById('severity-tags'))
            }
        }

        filteredData = filterData()

        updateBarChart(filteredData);
        updatePieChart(filteredData);
        updateSeverityBarChart(filteredData);
        updateRoadTypeBarChart(filteredData);
    }

    function updateGraphsOnly() {
        filteredData = filterData()

        updateBarChart(filteredData);
        updatePieChart(filteredData);
        updateSeverityBarChart(filteredData);
        updateRoadTypeBarChart(filteredData);
    }

    function startGraph() {
        try {
            // Remove duplicate records
            const uniqueData = Array.from(new Set(datedata.map(item => JSON.stringify(item))))
                .map(item => JSON.parse(item));

            // Debugging: Print unique data to console
            console.log('Unique Data:', uniqueData);

            // Check if there is any data to process
            if (uniqueData.length === 0) {
                throw new Error('No data available to render graphs.');
            }

            // Get unique batch IDs and sort them
            var ubatches = [...new Set(uniqueData.map(item => item.BatchID))];
            ubatches.sort((a, b) => parseInt(a) - parseInt(b));

            // Check if there are any batches
            if (ubatches.length === 0) {
                throw new Error('No batch IDs found in the data.');
            }

            // Get the latest batch ID
            var latestBatch = ubatches[ubatches.length - 1];

            // Add the latest batch tag
            addTag(latestBatch, bSet, document.getElementById('batch-tags'));

            // Filter data to include only the latest batch
            let filteredData = filterData();

            // Check if filtered data is empty
            if (filteredData.length === 0) {
                throw new Error('Filtered data is empty.');
            }

            // Update the graphs with the filtered data
            updateBarChart(filteredData);
            updatePieChart(filteredData);
            updateSeverityBarChart(filteredData);
            updateRoadTypeBarChart(filteredData);

        } catch (error) {
            console.error('Error in startGraph:', error);
            const errorElement = document.getElementById('error');
            if (errorElement) {
                errorElement.innerText = "Error loading data: " + error.message;
            } else {
                console.error('Error element not found.');
            }
        }
    }

    function clearFilters() {
        dSet.length = 0;
        mSet.length = 0;
        ySet.length = 0;
        tSet.length = 0;
        bSet.length = 0;
        defectSet.length = 0;
        typeSet.length = 0;
        severitySet.length = 0;

        document.getElementById('day-tags').innerHTML = '';
        document.getElementById('month-tags').innerHTML = '';
        document.getElementById('year-tags').innerHTML = '';
        document.getElementById('town-tags').innerHTML = '';
        document.getElementById('batch-tags').innerHTML = '';
        document.getElementById('defect-tags').innerHTML = '';
        document.getElementById('type-tags').innerHTML = '';
        document.getElementById('severity-tags').innerHTML = '';

        updateOptions(datedata);

        updateGraphsOnly(); // Optionally, update the graphs to reflect the cleared filters
    }

    function updateOptions(datedataCopy) {
        var dselect = document.getElementById('day-select');
        var mselect = document.getElementById('month-select');
        var yselect = document.getElementById('year-select');
        var tselect = document.getElementById('town-select');
        var bselect = document.getElementById('batch-select');
        var defectselect = document.getElementById('defect-select');
        var typeselect = document.getElementById('type-select');
        var severityselect = document.getElementById('severity-select');

        var dTemp = dselect.value
        var mTemp = mselect.value
        var yTemp = yselect.value
        var tTemp = tselect.value
        var bTemp = bselect.value
        var defectTemp = defectselect.value
        var typeTemp = typeselect.value
        var severityTemp = severityselect.value

        var utowns = [...new Set(datedataCopy.map(item => item.Town))];
        var udays = [...new Set(datedataCopy.map(item => item.D))];
        var umonths = [...new Set(datedataCopy.map(item => item.M))];
        var uyears = [...new Set(datedataCopy.map(item => item.Y))];
        var ubatches = [...new Set(datedataCopy.map(item => item.BatchID))];
        var udefects = [...new Set(datedataCopy.map(item => item['Layer Name']))];
        if (udefects.includes("AllDefect")) {
            udefects.splice(udefects.indexOf("AllDefect"), 1);
        }
        var utypes = [...new Set(datedataCopy.map(item => item.Type))];

        tselect.innerHTML = '<option value="Nil">Nil</option>'
        bselect.innerHTML = '<option value="Nil">Nil</option>'
        dselect.innerHTML = '<option value="Nil">Nil</option>'
        mselect.innerHTML = '<option value="Nil">Nil</option>'
        yselect.innerHTML = '<option value="Nil">Nil</option>'
        defectselect.innerHTML = '<option value="Nil" selected>Nil</option>'
        typeselect.innerHTML = '<option value="Nil" selected>Nil</option>'
        severityselect.innerHTML = '<option value="Nil" selected>Nil</option>'

        utowns = utowns.sort()
        uyears = uyears.sort()
        udays = udays.sort()
        ubatches.sort((a, b) => parseInt(a) - parseInt(b));
        udefects = udefects.sort()
        utypes = utypes.sort()

        const monthOrder = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        umonths = umonths.sort((a, b) => monthOrder.indexOf(a) - monthOrder.indexOf(b));
        datedataCopy.forEach(item => {
            item.Severity = item.Severity.toString()
            item.BatchID = item.BatchID.toString()
        })

        var useverities = [...new Set(datedataCopy.map(item => item.Severity))];

        if (useverities.includes("NULL")) {
            useverities.splice(useverities.indexOf("NULL"), 1);
            useverities.unshift("NULL");
        }

        if (utypes.includes("NULL")) {
            utypes.splice(utypes.indexOf("NULL"), 1);
            utypes.unshift("NULL");
        }

        utowns.forEach(utown => {
            var option = document.createElement('option');
            option.text = utown;
            option.value = utown;
            if (tSet.length != 0) {
                if (utown == tTemp) {
                    option.selected = true;
                }
            }
            tselect.add(option);
        });

        ubatches.forEach(ubatch => {
            var option = document.createElement('option');
            option.text = ubatch;
            option.value = ubatch;
            if (bSet.length != 0) {
                if (ubatch == bTemp) {
                    option.selected = true;
                }
            }
            bselect.add(option);
        })

        udays.forEach(uday => {
            var option = document.createElement('option');
            option.text = uday;
            option.value = uday;
            if (dSet.length != 0) {
                if (uday == dTemp) {
                    option.selected = true;
                }
            }
            dselect.add(option);

        })

        umonths.forEach(umonth => {
            var option = document.createElement('option');
            option.text = umonth;
            option.value = umonth;
            if (mSet.length != 0) {
                if (umonth == mTemp) {
                    option.selected = true;
                }
            }
            mselect.add(option);

        })

        uyears.forEach(uyear => {
            var option = document.createElement('option');
            option.text = uyear;
            option.value = uyear;
            if (ySet.length != 0) {
                if (uyear == yTemp) {
                    option.selected = true;
                }
            }
            yselect.add(option);
        })

        udefects.forEach(udefect => {
            var option = document.createElement('option');
            option.text = udefect;
            option.value = udefect;
            if (defectSet.length != 0) {
                if (udefect == defectTemp) {
                    option.selected = true;
                }
            }
            defectselect.add(option);
        })

        utypes.forEach(utype => {
            var option = document.createElement('option');
            option.text = utype;
            option.value = utype;
            if (typeSet.length != 0) {
                if (utype == typeTemp) {
                    option.selected = true;
                }
            }
            typeselect.add(option);
        })

        useverities.forEach(useverity => {
            var option = document.createElement('option');
            option.text = useverity;
            option.value = useverity;
            if (severitySet.length != 0) {
                if (useverity == severityTemp) {
                    option.selected = true
                }
            }
            severityselect.add(option);
        })
    }

    var dSet = []
    var mSet = []
    var ySet = []
    var tSet = []
    var bSet = []
    defectSet = []
    typeSet = []
    severitySet = []

    function arraysEqual(arr1, arr2) {
        if (arr1.length !== arr2.length) {
            return false;
        }
        for (let i = 0; i < arr1.length; i++) {
            if (arr1[i] !== arr2[i]) {
                return false;
            }
        }
        return true;
    }

    function looseIncludes(collection, value) {
        if (typeof collection === 'string') {
            return collection.indexOf(String(value)) !== -1;
        } else if (Array.isArray(collection)) {
            return collection.some(item => item == value);
        }
        return false;
    }

    function filterData() {

        var datedataCopy = [...datedata]

        if (typeSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(typeSet, item.Type))
        }

        if (severitySet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(severitySet, item.Severity))
        }

        if (defectSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(defectSet, item['Layer Name']))
        }

        if (tSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(tSet, item.Town));
        }

        if (dSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(dSet, item.D));
        }

        if (mSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(mSet, item.M));
        }

        if (ySet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(ySet, item.Y));
        }

        if (bSet.length != 0) {
            datedataCopy = datedataCopy.filter(item => looseIncludes(bSet, item.BatchID));
        }

        updateOptions(datedata);

        if (datedataCopy.length === 0) {
            displayNoDataMessage();
            return [];
        }

        showGraphs();
        return datedataCopy;
    }

    function displayNoDataMessage() {
        const noDataMessage = "<html><body><h1>No records found</h1></body></html>";
        const webViewElement = document.getElementById("noRecords");
        if (webViewElement) {
            webViewElement.innerHTML = noDataMessage;
        }

        const graphContainers = document.querySelectorAll('.graph-container');
        graphContainers.forEach(container => {
            container.style.display = 'none';
        });
    }

    function showGraphs() {
        const webViewElement = document.getElementById("noRecords");
        if (webViewElement) {
            webViewElement.innerHTML = "";
        }

        const graphContainers = document.querySelectorAll('.graph-container');
        graphContainers.forEach(container => {
            container.style.display = 'block';
        });
    }

    function updateBarChart(filteredData) {

        var defectCounts = {};
        console.log("Filtered Data" + filteredData);
        filteredData.forEach(row => {
            defectCounts[row.Road] = (defectCounts[row.Road] || 0) + 1;
        });
        console.log("Defect counts:", defectCounts);
        var defectCountsValues = [];
        for (var key in defectCounts) {
            if (defectCounts.hasOwnProperty(key)) {
                var value = defectCounts[key];
                defectCountsValues.push(value);
            }
        }

        var trace = {
            y: Object.keys(defectCounts),
            x: defectCountsValues,
            type: 'bar',
            orientation: 'h',
            marker: { color: defectCountsValues, colorscale: 'Portland' },
            transforms: [{
                type: 'sort',
                target: 'x',
                order: 'ascending'
            }],
            text: defectCountsValues.map(String),
            textposition: 'inside',
            hovertemplate: 'Count: %{x}<extra></extra>'
        };

        var layout = {
            title: 'Defect Count by Road Address',
            yaxis: {
                title: 'Road Address',
            },
            xaxis: {
                title: 'Defect Count',
            },
            width: 800,
            margin: {
                l: 200,
            }
        };

        Plotly.newPlot('town-graph', [trace], layout);
        console.log("Graph updated");
    }

    function updatePieChart(filteredData) {

        var defectTypes = {};
        filteredData.forEach(row => {
            defectTypes[row.Type] = (defectTypes[row.Type] || 0) + 1;
        });
        console.log("Defect types:", defectTypes);

        var values = [];
        for (var key in defectTypes) {
            if (defectTypes.hasOwnProperty(key)) {
                values.push(defectTypes[key]);
            }
        }

        var labels = Object.keys(defectTypes);

        var trace = {
            labels: labels,
            values: values,
            type: 'pie',
            textinfo: 'label+percent',
            textposition: 'inside',
            insidetextorientation: 'radial',
            hovertemplate: 'Defect Type: %{label}<br>Count: %{value}}<br>Percentage: %{percent}}<extra></extra>',
        };

        var layout = {
            title: 'Defect Distribution by Defect Type',
            width: 800,
            margin: {
                l: 200,
            }

        }

        Plotly.newPlot('pie-chart-defect', [trace], layout);
        console.log("Pie chart updated");
    }

    function updateSeverityBarChart(filteredData) {
        var defectSeverityCounts = {};
        filteredData.forEach(row => {
            if (!defectSeverityCounts[row.Type]) {
                defectSeverityCounts[row.Type] = {};
            }
            defectSeverityCounts[row.Type][row.Severity] = (defectSeverityCounts[row.Type][row.Severity] || 0) + 1;
        });
        console.log("Defect severity counts:", defectSeverityCounts);
    
        var defectTypes = Object.keys(defectSeverityCounts);
        var severityLevels = Array.from(new Set(filteredData.map(row => row.Severity)));
    
        var colors = ['#EF553B', '#00CC96', '#636EFA', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'];
    
        // Create an array of objects to hold the counts for each defect type
        var defectTypeCounts = defectTypes.map(type => {
            var totalCounts = severityLevels.reduce((sum, severity) => sum + (defectSeverityCounts[type][severity] || 0), 0);
            return { type, totalCounts };
        });
    
        // Sort the defect types by their total count in descending order
        defectTypeCounts.sort((a, b) => b.totalCounts - a.totalCounts);
    
        var sortedDefectTypes = defectTypeCounts.map(item => item.type);
    
        var traces = severityLevels.map(function (severity, index) {
            return {
                y: sortedDefectTypes.map(function (type) {
                    return defectSeverityCounts[type][severity] || 0;
                }),
                x: sortedDefectTypes,
                type: 'bar',
                name: 'Severity: ' + severity,
                marker: { color: colors[index % colors.length] },
                text: sortedDefectTypes.map(function (type) {
                    return (defectSeverityCounts[type][severity] || 0).toString();
                }),
                textposition: 'inside',
                hovertemplate: 'Defect Type: %{x}<br>Severity: ' + severity + '<br>Count: %{y}<extra></extra>'
            };
        });
    
        var layout = {
            title: 'Defect Type by Severity Distribution',
            yaxis: {
                title: 'Severity Count',
            },
            xaxis: { title: 'Defect Type' },
            width: 800,
            margin: {
                l: 200
            },
            barmode: 'stack',
            showlegend: true
        };
    
        Plotly.newPlot('severity-bar-chart', traces, layout);
        console.log("Severity bar chart updated");
    }
    
    function updateRoadTypeBarChart(filteredData) {
        var defectCounts = {};
        var totalCounts = {};

        filteredData.forEach(row => {
            if (!defectCounts[row.Type]) {
                defectCounts[row.Type] = {};
            }
            defectCounts[row.Type][row.RoadType] = (defectCounts[row.Type][row.RoadType] || 0) + 1;
            totalCounts[row.Type] = (totalCounts[row.Type] || 0) + 1;
        });
        console.log("Defect counts by road type:", defectCounts);
        console.log("Total counts by defect type:", totalCounts);

        var sortedDefectTypes = Object.keys(totalCounts).sort(function (a, b) {
            return totalCounts[b] - totalCounts[a];
        });

        var roadTypes = Array.from(new Set(filteredData.map(row => row.RoadType)));
        var colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52'];

        var traces = roadTypes.map(function (roadType, index) {
            var y_values = sortedDefectTypes.map(function (type) {
                return defectCounts[type][roadType] || 0;
            });

            return {
                x: sortedDefectTypes,
                y: y_values,
                type: 'bar',
                name: roadType,
                marker: { color: colors[index % colors.length] },
                text: y_values.map(String),
                textposition: 'inside',
                hovertemplate: 'Defect Type: %{x}<br>Road Type: ' + roadType + '<br>Count: %{y}<extra></extra>'
            };
        });
        var layout = {
            title: 'Defect Type by Road Type Distribution',
            xaxis: { title: 'Defect Type' },
            yaxis: {
                title: 'Defect Count',
            },
            width: 800,
            margin: {
                l: 200
            },
            barmode: 'group',
            showlegend: true,
        };

        Plotly.newPlot('road-type-bar-chart', traces, layout);
        console.log("Road type bar chart updated");
    }

    // Function to decompress base64 encoded gzip data
    function decompressData(base64Data) {
        const binaryString = atob(base64Data);
        const len = binaryString.length;
        const bytes = new Uint8Array(len);
        for (let i = 0; i < len; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        const decompressed = pako.inflate(bytes, { to: 'string' });
        return JSON.parse(decompressed);
    }


    // Decompress the embedded data
    const jsonData = decompressData(compressedJsonData);

    document.addEventListener('DOMContentLoaded', function() {
        try {
            window.datedata = jsonData;
            startGraph();
        } catch (error) {
            console.error('Error loading data:', error);
            document.getElementById("error").innerText = "Error loading data: " + error;
        }
    });




} catch (error) {
    var errorMessage = "<strong>Error Occurred!</strong><br><br>";
    errorMessage += "<strong>Error Name:</strong> " + error.name + "<br>";
    errorMessage += "<strong>Error Message:</strong> " + error.message + "<br><br>";
    errorMessage += "<strong>Occurred At:</strong> " + new Date().toLocaleString() + "<br><br>";
    errorMessage += "<strong>Error Stack Trace:</strong><br>" + error.stack + "<br><br>";

    if (error.lineNumber && error.columnNumber) {
        errorMessage += "<strong>Error Location:</strong> Line " + error.lineNumber + ", Column " + error.columnNumber + "<br><br>";
    }

    var codeSnippet = "Relevant code snippet here";
    errorMessage += "<strong>Code Snippet:</strong><br><pre>" + codeSnippet + "</pre><br><br>";

    var additionalContext = "User actions that led to the error.";
    errorMessage += "<strong>Additional Context:</strong><br>" + additionalContext + "<br><br>";

    var possibleSolutions = "Check the JSON syntax for invalid characters.";
    errorMessage += "<strong>Possible Solutions:</strong><br>" + possibleSolutions;

    var errorContainer = document.getElementById("error");
    errorContainer.innerHTML += "<br>";
    errorContainer.innerHTML += errorMessage;
}
