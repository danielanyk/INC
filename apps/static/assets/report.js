document.addEventListener("DOMContentLoaded", function () {
    defaultbatch = document.querySelector(BATCH_SELECTOR).value;;
    fetchReports(defaultbatch, '', '', '', '', 'Invalid date', 'undefined');
    document.getElementById('apply').addEventListener('click', getAllTags);
    document.getElementById('clearAll').addEventListener('click', function() {
        var defectCheckboxes = document.querySelectorAll('#dropdown2 input[type="checkbox"]');
        defectCheckboxes.forEach(function(checkbox) {
            checkbox.checked = false;
        });
        document.getElementById('severity').value = "";
        document.getElementById('town').value = "";
        document.getElementById('custom_tags').value = "";
        document.getElementById('batch').value = "";
    });
    $(function() {
              
        $('input[name="datefilter"]').daterangepicker({
            autoUpdateInput: false,
            locale: {
                cancelLabel: 'Clear'
            }
        });
      
        $('input[name="datefilter"]').on('apply.daterangepicker', function(ev, picker) {
            $(this).val(picker.startDate.format('D/M/YYYY') + ' - ' + picker.endDate.format('D/M/YYYY'));
            getAllTags();
        });
      
        $('input[name="datefilter"]').on('cancel.daterangepicker', function(ev, picker) {
            $(this).val('');
            document.getElementsByName('datefilter').value = "";
            window.location.reload();
        });
      
      });
    document.getElementById("fulldownload").addEventListener("click", DownloadAllReports);
    document.getElementById("viewmore").addEventListener("click", View30More);
    document.getElementById("generateSummary").addEventListener("click", generateSummarizerHandler);
});

var checkedReports = []
const DATE_FILTER_SELECTOR = 'input[name="datefilter"]';
const SEVERITY_SELECTOR = '#severity';
const TOWN_SELECTOR = '#town';
const CUSTOM_TAGS_SELECTOR = '#custom_tags';
const DEFECT_CHECKBOXES_SELECTOR = '#dropdown2 input[type="checkbox"]';
const BATCH_SELECTOR = '#batch';
const defectClasses = {
    'Alligator Crack': { class: 'bg-emerald-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Arrow': { class: 'bg-yellow-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Block Crack': { class: 'bg-green-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Damaged Base Crack': { class: 'bg-blue-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Localise Surface Defect': { class: 'bg-indigo-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Multi Crack': { class: 'bg-purple-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Parallel Lines': { class: 'bg-pink-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Peel Off With Cracks': { class: 'bg-red-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Peeling Off Premix': { class: 'bg-emerald-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Pothole With Crack': { class: 'bg-green-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Rigid Pavement Crack': { class: 'bg-blue-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Single Crack': { class: 'bg-indigo-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Transverse Crack': { class: 'bg-purple-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Wearing Course Peeling Off': { class: 'bg-pink-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'White Lane': { class: 'bg-white text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Yellow Lane': { class: 'bg-amber-200 text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Raveling': { class: 'bg-green-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Faded Kerb': { class: 'bg-blue-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' },
    'Paint Spillage': { class: 'bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' }
  };

const QUANTITY_SELECTOR = '#quantity';
const MEASUREMENT_SELECTOR = '#measurement';
const CAUSE_SELECTOR = '#cause';
const RECOMMENDATION_SELECTOR = '#recommendation';
const REMARKS_SELECTOR = '#remarks';
const SUPERVISOR_SELECTOR = '#supervisor';
const VIA_SELECTOR = '#via';
const ACKNOWLEDGEMENT_SELECTOR = '#acknowledgement';



function getCheckedCheckboxes(selector) {
    const checkboxes = document.querySelectorAll(selector);
    const checkedValues = Array.from(checkboxes)
        .filter(checkbox => checkbox.checked)
        .map(checkbox => checkbox.value);

    return checkedValues;
}

function getAllTags() {
    const severity = document.querySelector(SEVERITY_SELECTOR).value;
    const town = document.querySelector(TOWN_SELECTOR).value;
    const customTags = document.querySelector(CUSTOM_TAGS_SELECTOR).value;
    const defectFilters = getCheckedCheckboxes(DEFECT_CHECKBOXES_SELECTOR);
    const batch = document.querySelector(BATCH_SELECTOR).value;
    const selectedDateRange = document.querySelector(DATE_FILTER_SELECTOR).value;
    const [startDate, endDate] = selectedDateRange.split(' - ');
    fetchReports(batch, defectFilters, severity, customTags, town, startDate, endDate);
}


function fetchReports(batch, defectFilters, severity, customTags, town, startDate, endDate) {
    
    fetch('/get_reports', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            batches: batch,
            defects: defectFilters,
            severity: severity,
            custom_tags: customTags,
            location: town,
            startDate: startDate, 
            endDate: endDate
        }),
    })
    .then(response => response.json())
    .then(data => {

        // Clear the existing content
        document.getElementById("reportContainer").innerHTML = '';

        // Loop over the data and populate the table rows
        data.forEach(report => {
            var row = document.createElement("tr");

            var nameCell = document.createElement("td");
            nameCell.className = "p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white";
            nameCell.textContent = report['Name'].split(".")[0];
            row.appendChild(nameCell);

            var inspectionDateCell = document.createElement("td");
            inspectionDateCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            inspectionDateCell.textContent = report['Inspection Date'];
            row.appendChild(inspectionDateCell);

            var inspectionTypeCell = document.createElement("td");
            inspectionTypeCell.className = "p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white text-center";
            inspectionTypeCell.textContent = report['Inspection Type'];
            row.appendChild(inspectionTypeCell);

            var inspectorCell = document.createElement("td");
            inspectorCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            inspectorCell.textContent = report['Inspector'];
            row.appendChild(inspectorCell);

            var defectCell = document.createElement("td");
            defectCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            
            report['Type'].forEach((type, index) => {
                if (type.includes("Faded Kerb")) {
                    type = "Faded Kerb";
                }
                
                if (type in defectClasses) {
                    var defectClass = defectClasses[type];
                
                } else {
                    defectClass = { class: 'bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' }
                }

                var severity = report['Severity'][index];
                var concatBorder = "";

                if (severity === 1) {
                    concatBorder = "border-4 border-amber-400";
                } else if (severity === 2) {
                    concatBorder = "border-4 border-orange-500";
                } else if (severity === 3) {
                    concatBorder = "border-4 border-red-600";
                }
            
                var defectSpan = document.createElement("span");
                defectSpan.className = `inline-block ${concatBorder} px-2 py-1 rounded-md ${defectClass.class}`;
                defectSpan.textContent = type;
            
                defectCell.appendChild(defectSpan);
                
            });
            row.appendChild(defectCell);

            var generationDateCell = document.createElement("td");
            generationDateCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            generationDateCell.textContent = report['Generation Date'];
            row.appendChild(generationDateCell);

            var viewButtonCell = document.createElement("td");
            viewButtonCell.className = "inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            var viewButton = document.createElement("button");

            viewButton.className = "view-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            viewButton.textContent = "View";
            viewButton.addEventListener("click", function(event) {
                viewButtonHandler(event, report);
            });
            viewButtonCell.appendChild(viewButton);
            row.appendChild(viewButtonCell);

            var editButtonCell = document.createElement("td");
            editButtonCell.className = "p-4 whitespace-nowrap";
            var editButton = document.createElement("button");

            editButton.className = "edit-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", function(event) {
                editButtonHandler(event, report);
            });
            editButtonCell.appendChild(editButton);
            row.appendChild(editButtonCell);

            var modalContainer = document.createElement("div");
            modalContainer.id = "default-modal";
            modalContainer.className = "hidden overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-50 flex justify-center items-center w-full md:inset-0 h-[calc(100%-1rem)] max-h-full bg-gray-900 bg-opacity-50";
            modalContainer.style.paddingTop = "120px"; 
            modalContainer.style.paddingBottom = "150px";
            var modalContent = `
                <div class="relative p-4 w-full max-w-2xl max-h-full">
                    <div class="relative bg-white rounded-lg shadow dark:bg-gray-700">
                        <div class="flex items-center justify-between p-4 md:p-5 border-b rounded-t dark:border-gray-600">
                            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Edit Report Details</h3>
                            <button data-modal-hide="default-modal" type="button" onclick="handleExitClick()" class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white" data-modal-hide="default-modal">
                                <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
                                </svg>
                                <span class="sr-only">Close modal</span>
                            </button>
                        </div>

                        <div class="p-4 md:p-5 space-y-4">
                            <form>
                                <div class="grid gap-4 md:grid-cols-2">
                                      <div>
                                          <label for="quantity" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Quantity</label>
                                          <input type="text" id="quantity" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="1 Member"/>
                                      </div>
                                      <div>
                                        <label for="measurement" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Measurement</label>
                                        <input type="text" id="measurement" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="1cm"/>
                                      </div>
                                      <div>
                                        <label for="cause" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Cause of Defect</label>
                                        <input type="text" id="cause" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Hit By Vehicle"/>
                                      </div>
                                      <div>
                                        <label for="recommendation" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Recommendation</label>
                                        <input type="text" id="recommendation" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Fill up pothole"/>
                                      </div>
                                      <div>
                                        <label for="remarks" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Remarks/Others</label>
                                        <input type="text" id="remarks" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Follow Up"/>
                                      </div>
                                      <div>
                                        <label for="supervisor" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Supervisor</label>
                                        <input type="text" id="supervisor" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder=${report["Inspector"]}/>
                                      </div>
                                      <div>
                                        <label for="via" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Reported Via</label>
                                        <input type="text" id="via" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Method / Agency / Date / Time"/>
                                      </div>
                                      <div>
                                        <label for="acknowledgement" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Acknowledgement</label>
                                        <input type="text" id="acknowledgement" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Method / Date / Time"/>
                                      </div>
                                </div>
                            </form>
                            <div>
                                <p class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Last Edited ${report['Generation Date']}</p>
                            </div>
                        </div>
                        <div class="flex items-center p-4 md:p-5 border-t border-gray-200 rounded-b dark:border-gray-600">
                            <button data-modal-hide="default-modal" type="button" onclick="handleConfirmClick()" class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Confirm</button>
                            <button data-modal-hide="default-modal" type="button" onclick="handleClearAll()" class="py-2.5 px-5 ms-3 text-sm font-medium text-gray-900 focus:outline-none bg-white rounded-lg border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-4 focus:ring-gray-100 dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700">Clear</button>
                        </div>
                    </div>
                </div>
            `;

            modalContainer.innerHTML = modalContent;
            document.body.appendChild(modalContainer);

            var downloadButtonCell = document.createElement("td");
            downloadButtonCell.className = "p-4 whitespace-nowrap";
            var downloadButton = document.createElement("button");
            downloadButton.id = "download-button-" + report['ReportID'];
            downloadButton.className = "download-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            downloadButton.textContent = "Download";

            downloadButton.addEventListener("click", function(event) {
                downloadButtonHandler(event, report);
            });
            downloadButtonCell.appendChild(downloadButton);
            row.appendChild(downloadButtonCell);


            var templateSelectCell = document.createElement("td");
            templateSelectCell.className = "p-4 whitespace-nowrap";
            var templateSelect = document.createElement("select");
            templateSelect.className = "mb-4 sm:mb-0 mr-4 inline-flex items-center text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2.5 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700";
            templateSelect.id = "templates";
            templateSelect.name = "templates";
            templateSelect.addEventListener("change", handleDropdownChange2);
            templateSelect.innerHTML = `<option value="Template1">Template 1</option>
                                        <option value="Template2">Template 2</option>
                                        <option value="Template3">Template 3</option>`;
            templateSelectCell.appendChild(templateSelect);
            row.appendChild(templateSelectCell);

            var newTagInputCell = document.createElement("td");
            newTagInputCell.className = "p-4 whitespace-nowrap";
            var newTagInput = document.createElement("input");
            newTagInput.className = "addtags mb-4 sm:mb-0 mr-4 inline-flex items-center text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2.5 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700";
            newTagInput.setAttribute("type", "text");
            newTagInput.setAttribute("placeholder", "Separate tags with commas");
            newTagInput.addEventListener("keypress", function(event) {

                if(event.key === 'Enter') {

                    fetch('/add_tags', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            report_id: report['ReportID'],
                            tags: newTagInput.value
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        if(alert(data)){}
                        else window.location.reload(); 
                        newTagInput.value = "";
            
                    });
                }

            })
            newTagInputCell.appendChild(newTagInput);
            row.appendChild(newTagInputCell);

            document.getElementById("reportContainer").appendChild(row);

            var summarizerCheckbox = document.createElement("td");
            summarizerCheckbox.className = "p-4 whitespace-nowrap text-center";
            var summarizerInput = document.createElement("input");
            summarizerInput.className = "summarizer-checkbox-" + report['ReportID'];
            summarizerInput.setAttribute("type", "checkbox");
            summarizerInput.addEventListener("click", function(event) {
                summarizerHandler(event, report);
            });
            summarizerCheckbox.appendChild(summarizerInput);
            row.appendChild(summarizerCheckbox);

            
        });
    })
    .catch(error => console.error('Error:', error));

}

function editButtonHandler(event, report) {
    currentReport = report;
    var modal = document.getElementById("default-modal");
    modal.classList.remove("hidden");
    modal.setAttribute("aria-hidden", "false");
    document.body.style.overflow = 'hidden';
}

var tempviewreport = "";
function handleConfirmClick() {
    var modal = document.getElementById("default-modal");
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    const quantity = document.querySelector(QUANTITY_SELECTOR).value;
    const measurement = document.querySelector(MEASUREMENT_SELECTOR).value;
    const cause = document.querySelector(CAUSE_SELECTOR).value;
    const recommendation = document.querySelector(RECOMMENDATION_SELECTOR).value;
    const remarks = document.querySelector(REMARKS_SELECTOR).value;
    const supervisor = document.querySelector(SUPERVISOR_SELECTOR).value;
    const via = document.querySelector(VIA_SELECTOR).value;
    const acknowledgement = document.querySelector(ACKNOWLEDGEMENT_SELECTOR).value;

    if (quantity != "" && measurement != "" && cause != "" && recommendation != "" && supervisor != "" && via != "" && acknowledgement != "") {
        fetch('/update_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                report_id: currentReport['ReportID'],
                quantity: quantity,
                measurement: measurement,
                cause: cause,
                recommendation: recommendation,
                remarks: remarks,
                supervisor: supervisor,
                via: via,
                acknowledgement: acknowledgement
            }),
        })
        .then(response => response.json())
        .then(data => {
            
            console.log(data);
            fetch('/generate_report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: currentReport['Name'],
                    ins_type: currentReport['Inspection Type'],
                    ins_date: currentReport['Inspection Date'],
                    road_type: currentReport['RoadType'],
                    type: currentReport['Type'],
                    latitude: currentReport['Latitude'],
                    longitude: currentReport['Longitude'],
                    inspector: currentReport['Inspector'],
                    severity: parseInt(currentReport['Severity']),
                    image: currentReport['Image'],
                    template: '1',
                    report_id: currentReport['ReportID'],
                    road: currentReport['Road'],
                    imageID: currentReport['ImageID'],
                    quantity: quantity,
                    measurement: measurement,
                    cause: cause,
                    recommendation: recommendation,
                    remarks: remarks,
                    supervisor: supervisor,
                    via: via,
                    acknowledgement: acknowledgement,
                    placeholder: "download"
                }),
              })
              .then(response => response.json())
              .then(data => {
                console.log(data);
                tempviewreport = data;
                console.log(tempviewreport);
              });
            

        })
        .catch(error => {
            // Handle fetch error
            console.error('Error:', error);
        });
        
        document.body.style.overflow = 'auto';
        return;
    }
    else {
        alert("Please fill in all fields");
        document.body.style.overflow = 'auto';
    }
}

function handleClearAll() {
    document.getElementById('quantity').value = "";
    document.getElementById('measurement').value = "";
    document.getElementById('cause').value = "";
    document.getElementById('recommendation').value = "";
    document.getElementById('remarks').value = "";
    document.getElementById('supervisor').value = "";
    document.getElementById('via').value = "";
    document.getElementById('acknowledgement').value = "";
}

function handleExitClick() {
    var modal = document.getElementById("default-modal");
    modal.classList.add("hidden");
    modal.setAttribute("aria-hidden", "true");
    document.body.style.overflow = 'auto';
    
}

function handleDropdownChange2 (){
  var templatesDropdown = document.getElementById("templates");
  var selectedTemplate = templatesDropdown.value;
}

// View buttons 
function viewButtonHandler(event, report) {
    var reportData = report;
    var selectedTemplate = event.target.closest('tr').querySelector("#templates").value;

    if (tempviewreport === "" | selectedTemplate != 'Template1') {
        fetch('/generate_report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: reportData['Name'],
                ins_type: reportData['Inspection Type'],
                ins_date: reportData['Inspection Date'],
                road_type: reportData['RoadType'],
                type: reportData['Type'],
                latitude: reportData['Latitude'],
                longitude: reportData['Longitude'],
                inspector: reportData['Inspector'],
                severity: parseInt(reportData['Severity']),
                image: reportData['Image'],
                template: selectedTemplate,
                report_id: reportData['ReportID'],
                road: reportData['Road'],
                imageID: reportData['ImageID'],
                quantity: reportData['Quantity'],
                measurement: reportData['Measurement'],
                cause: reportData['Cause'],
                recommendation: reportData['Recommendation'],
                remarks: reportData['Remarks'],
                supervisor: reportData['Supervisor'],
                via: reportData['Via'],
                acknowledgement: reportData['Acknowledgement'],
                placeholder: "temp"
            }),
        })
        .then(response => response.json())
        .then(data => {
        
            fetch('/view_temp', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    path: data,
                }),
            });
        });
    } 
    else {
        fetch('/view_temp', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                path: tempviewreport,
            }),
        })
        .then(response => response.json())
        .then(data => {
            window.location.reload();
        })
    }
}
    
function downloadButtonHandler(event, report) {
    var reportData = report;
    var selectedTemplate = event.target.closest('tr').querySelector("#templates").value;

    fetch('/generate_report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            name: reportData['Name'],
            ins_type: reportData['Inspection Type'],
            ins_date: reportData['Inspection Date'],
            road_type: reportData['RoadType'],
            type: reportData['Type'],
            latitude: reportData['Latitude'],
            longitude: reportData['Longitude'],
            inspector: reportData['Inspector'],
            severity: parseInt(reportData['Severity']),
            image: reportData['Image'],
            template: selectedTemplate,
            report_id: reportData['ReportID'],
            road: reportData['Road'],
            imageID: reportData['ImageID'],
            quantity: reportData['Quantity'],
            measurement: reportData['Measurement'],
            cause: reportData['Cause'],
            recommendation: reportData['Recommendation'],
            remarks: reportData['Remarks'],
            supervisor: reportData['Supervisor'],
            via: reportData['Via'],
            acknowledgement: reportData['Acknowledgement'],
            placeholder: "download"
        }),
      })
      .then(response => response.json())
      .then(data => {
        alert("Report downloaded successfully to\n" + data);
      });
}

function DownloadAllReports() {
    const downloadButtons = document.querySelectorAll(".download-button");

    downloadButtons.forEach(button => {
        button.click();
    });
    if (downloadButtons.length == 0) {
        alert("No reports to download");
    }
    else {
    alert("All reports downloaded successfully")};
}

// Add new tags
function addtags(ele) {
    if(event.key === 'Enter') {
        alert(ele.value); 
        var reportData = JSON.parse(event.target.closest('tr').dataset.report); 
        

        fetch('/add_tags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                report_id: reportData['ReportID'],
                tags: stringify(ele.value)
            }),
        })
        .then(response => response.json())
        .then(data => {
            if(alert(data)){}
            else window.location.reload(); 
            ele.value = "";

        });
    }
}

// Get the next 30 reports
function View30More() {
    
    const severity = document.querySelector(SEVERITY_SELECTOR).value;
    const town = document.querySelector(TOWN_SELECTOR).value;
    const customTags = document.querySelector(CUSTOM_TAGS_SELECTOR).value;
    const defectFilters = getCheckedCheckboxes(DEFECT_CHECKBOXES_SELECTOR);
    const batch = document.querySelector(BATCH_SELECTOR).value;
    const selectedDateRange = document.querySelector(DATE_FILTER_SELECTOR).value;
    const [startDate, endDate] = selectedDateRange.split(' - ');

    fetch('/load_more', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            batches: batch,
            defects: defectFilters,
            severity: severity,
            custom_tags: customTags,
            location: town,
            startDate: startDate, 
            endDate: endDate,
            startindex: document.getElementById("reportContainer").childElementCount,
            endindex: document.getElementById("reportContainer").childElementCount + 30
        }),
    })
    .then(response => response.json())
    .then(data => {

        const filteredData = data.filter(report => !report.Image.includes(batch));
        console.log(filteredData);
        if (filteredData.length != 0) {
            data = filteredData;
        }

        data.forEach(report => {
            var row = document.createElement("tr");

            var nameCell = document.createElement("td");
            nameCell.className = "p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white";
            nameCell.textContent = report['Name'].split(".")[0];
            row.appendChild(nameCell);

            var inspectionDateCell = document.createElement("td");
            inspectionDateCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            inspectionDateCell.textContent = report['Inspection Date'];
            row.appendChild(inspectionDateCell);

            var inspectionTypeCell = document.createElement("td");
            inspectionTypeCell.className = "p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white text-center";
            inspectionTypeCell.textContent = report['Inspection Type'];
            row.appendChild(inspectionTypeCell);

            var inspectorCell = document.createElement("td");
            inspectorCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            inspectorCell.textContent = report['Inspector'];
            row.appendChild(inspectorCell);

            var defectCell = document.createElement("td");
            defectCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            
            report['Type'].forEach((type, index) => {
                if (type.includes("Faded Kerb")) {
                    type = "Faded Kerb";
                }
                
                if (type in defectClasses) {
                    var defectClass = defectClasses[type];
                
                } else {
                    defectClass = { class: 'bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md' }
                }

                var severity = report['Severity'][index];
                var concatBorder = "";

                if (severity === 1) {
                    concatBorder = "border-4 border-amber-400";
                } else if (severity === 2) {
                    concatBorder = "border-4 border-orange-500";
                } else if (severity === 3) {
                    concatBorder = "border-4 border-red-600";
                }
            
                var defectSpan = document.createElement("span");
                defectSpan.className = `inline-block ${concatBorder} px-2 py-1 rounded-md ${defectClass.class}`;
                defectSpan.textContent = type;
            
                defectCell.appendChild(defectSpan);
                
            });
            row.appendChild(defectCell);

            var generationDateCell = document.createElement("td");
            generationDateCell.className = "p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            generationDateCell.textContent = report['Generation Date'];
            row.appendChild(generationDateCell);

            var viewButtonCell = document.createElement("td");
            viewButtonCell.className = "inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400";
            var viewButton = document.createElement("button");

            viewButton.className = "view-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            viewButton.textContent = "View";
            viewButton.addEventListener("click", function(event) {
                viewButtonHandler(event, report);
            });
            viewButtonCell.appendChild(viewButton);
            row.appendChild(viewButtonCell);

            var editButtonCell = document.createElement("td");
            editButtonCell.className = "p-4 whitespace-nowrap";
            var editButton = document.createElement("button");

            editButton.className = "edit-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            editButton.textContent = "Edit";
            editButton.addEventListener("click", function(event) {
                editButtonHandler(event, report);
            });
            editButtonCell.appendChild(editButton);
            row.appendChild(editButtonCell);

            var modalContainer = document.createElement("div");
            modalContainer.id = "default-modal";
            modalContainer.className = "hidden overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-50 flex justify-center items-center w-full md:inset-0 h-[calc(100%-1rem)] max-h-full bg-gray-900 bg-opacity-50";
            modalContainer.style.paddingTop = "120px"; 
            modalContainer.style.paddingBottom = "150px";
            var modalContent = `
                <div class="relative p-4 w-full max-w-2xl max-h-full">
                    <div class="relative bg-white rounded-lg shadow dark:bg-gray-700">
                        <div class="flex items-center justify-between p-4 md:p-5 border-b rounded-t dark:border-gray-600">
                            <h3 class="text-xl font-semibold text-gray-900 dark:text-white">Edit Report Details</h3>
                            <button data-modal-hide="default-modal" type="button" onclick="handleExitClick()" class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm w-8 h-8 ms-auto inline-flex justify-center items-center dark:hover:bg-gray-600 dark:hover:text-white" data-modal-hide="default-modal">
                                <svg class="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 14">
                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m1 1 6 6m0 0 6 6M7 7l6-6M7 7l-6 6"/>
                                </svg>
                                <span class="sr-only">Close modal</span>
                            </button>
                        </div>

                        <div class="p-4 md:p-5 space-y-4">
                            <form>
                                <div class="grid gap-4 md:grid-cols-2">
                                      <div>
                                          <label for="quantity" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Quantity</label>
                                          <input type="text" id="quantity" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="1 Member"/>
                                      </div>
                                      <div>
                                        <label for="measurement" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Measurement</label>
                                        <input type="text" id="measurement" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="1cm"/>
                                      </div>
                                      <div>
                                        <label for="cause" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Cause of Defect</label>
                                        <input type="text" id="cause" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Hit By Vehicle"/>
                                      </div>
                                      <div>
                                        <label for="recommendation" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Recommendation</label>
                                        <input type="text" id="recommendation" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Fill up pothole"/>
                                      </div>
                                      <div>
                                        <label for="remarks" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Remarks/Others</label>
                                        <input type="text" id="remarks" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Follow Up"/>
                                      </div>
                                      <div>
                                        <label for="supervisor" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Supervisor</label>
                                        <input type="text" id="supervisor" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder=${report["Inspector"]}/>
                                      </div>
                                      <div>
                                        <label for="via" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Reported Via</label>
                                        <input type="text" id="via" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Method / Agency / Date / Time"/>
                                      </div>
                                      <div>
                                        <label for="acknowledgement" class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Acknowledgement</label>
                                        <input type="text" id="acknowledgement" class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Method / Date / Time"/>
                                      </div>
                                </div>
                            </form>
                            <div>
                                <p class="block mb-2 text-sm font-medium text-gray-900 dark:text-white">Last Edited ${report['Generation Date']}</p>
                            </div>
                        </div>
                        <div class="flex items-center p-4 md:p-5 border-t border-gray-200 rounded-b dark:border-gray-600">
                            <button data-modal-hide="default-modal" type="button" onclick="handleConfirmClick()" class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Confirm</button>
                            <button data-modal-hide="default-modal" type="button" onclick="handleClearAll()" class="py-2.5 px-5 ms-3 text-sm font-medium text-gray-900 focus:outline-none bg-white rounded-lg border border-gray-200 hover:bg-gray-100 hover:text-blue-700 focus:z-10 focus:ring-4 focus:ring-gray-100 dark:focus:ring-gray-700 dark:bg-gray-800 dark:text-gray-400 dark:border-gray-600 dark:hover:text-white dark:hover:bg-gray-700">Clear</button>
                        </div>
                    </div>
                </div>
            `;

            modalContainer.innerHTML = modalContent;
            document.body.appendChild(modalContainer);

            var downloadButtonCell = document.createElement("td");
            downloadButtonCell.className = "p-4 whitespace-nowrap";
            var downloadButton = document.createElement("button");
            downloadButton.id = "download-button-" + report['ReportID'];
            downloadButton.className = "download-button inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700";
            downloadButton.textContent = "Download";

            downloadButton.addEventListener("click", function(event) {
                downloadButtonHandler(event, report);
            });
            downloadButtonCell.appendChild(downloadButton);
            row.appendChild(downloadButtonCell);


            var templateSelectCell = document.createElement("td");
            templateSelectCell.className = "p-4 whitespace-nowrap";
            var templateSelect = document.createElement("select");
            templateSelect.className = "mb-4 sm:mb-0 mr-4 inline-flex items-center text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2.5 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700";
            templateSelect.id = "templates";
            templateSelect.name = "templates";
            templateSelect.addEventListener("change", handleDropdownChange2);
            templateSelect.innerHTML = `<option value="Template1">Template 1</option>
                                        <option value="Template2">Template 2</option>
                                        <option value="Template3">Template 3</option>`;
            templateSelectCell.appendChild(templateSelect);
            row.appendChild(templateSelectCell);

            var newTagInputCell = document.createElement("td");
            newTagInputCell.className = "p-4 whitespace-nowrap";
            var newTagInput = document.createElement("input");
            newTagInput.className = "addtags mb-4 sm:mb-0 mr-4 inline-flex items-center text-gray-900 bg-white border border-gray-300 focus:outline-none hover:bg-gray-100 focus:ring-4 focus:ring-gray-200 font-medium rounded-lg text-sm px-4 py-2.5 dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:hover:bg-gray-700 dark:hover:border-gray-600 dark:focus:ring-gray-700";
            newTagInput.setAttribute("type", "text");
            newTagInput.setAttribute("placeholder", "Separate tags with commas");
            newTagInput.addEventListener("keypress", function(event) {

                if(event.key === 'Enter') {

                    fetch('/add_tags', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            report_id: report['ReportID'],
                            tags: newTagInput.value
                        }),
                    })
                    .then(response => response.json())
                    .then(data => {
                        if(alert(data)){}
                        else window.location.reload(); 
                        newTagInput.value = "";
            
                    });
                }

            })
            newTagInputCell.appendChild(newTagInput);
            row.appendChild(newTagInputCell);

            document.getElementById("reportContainer").appendChild(row);

            var summarizerCheckbox = document.createElement("td");
            summarizerCheckbox.className = "p-4 whitespace-nowrap text-center";
            var summarizerInput = document.createElement("input");
            summarizerInput.className = "summarizer-checkbox-" + report['ReportID'];
            summarizerInput.setAttribute("type", "checkbox");
            summarizerInput.addEventListener("click", function(event) {
                summarizerHandler(event, report);
            });
            summarizerCheckbox.appendChild(summarizerInput);
            row.appendChild(summarizerCheckbox);
        });
    });
}

function summarizerHandler(event, report) {
    var input = event.target;

    if (input.checked) {
        if (!checkedReports.some(r => r.ReportID === report.ReportID)) {
            checkedReports.push(report);
        }
    } else {
        checkedReports = checkedReports.filter(r => r.ReportID !== report.ReportID);
    }
}

function generateSummarizerHandler() {
    console.log('checked reports: ', checkedReports);
    function formatReport(data) {
        if (data.length === 0) {
            return '';
        }
    
        return data.map(item => {
            const combinedReport = {
                reportID: item.ReportID,
                inspectedBy: item.Inspector,
                inspectionDate: item["Inspection Date"],
                generationTime: item["Generation Date"],
                tags: [],
                defects: [],
                defectLikelihoods: [],
                severity: []
            };
    
            item.Type.forEach((type, index) => {
                combinedReport.tags.push(item["Custom Tag"][index] || "None");
                combinedReport.defects.push(type);
                combinedReport.defectLikelihoods.push(item.Confidence[index] || 0);
                combinedReport.severity.push(item.Severity[index] || 0);
            });
    
            return `ReportID: ${combinedReport.reportID}\n` +
                   `InspectedBy: ${combinedReport.inspectedBy},\n` +
                   `InspectionDate: ${combinedReport.inspectionDate},\n` +
                   `GenerationTime: ${combinedReport.generationTime},\n` +
                   `Tags: [${combinedReport.tags.join(", ")}],\n` +
                   `Defect(s): [${combinedReport.defects.join(", ")}],\n` +
                   `DefectLikelihood(s): [${combinedReport.defectLikelihoods.join(", ")}], \n` +
                   `Severity: [${combinedReport.severity.join(", ")}],\n`;
        }).join('\n');
    }
    
    let text = formatReport(checkedReports);
    let summaryStyle = document.getElementById('summaryStyle').value;
    let estimatedTimeInSeconds = text.length * 0.1;


    let estimatedTime;
    if (estimatedTimeInSeconds < 60) {
        estimatedTime = `${estimatedTimeInSeconds.toFixed(0)} seconds`;
        if (estimatedTimeInSeconds < 40) {
            estimatedTime = `40 seconds`;
        }
    } else if (estimatedTimeInSeconds < 3600) {
        estimatedTime = `${(estimatedTimeInSeconds / 60).toFixed(0)} minute(s)`;
    } else {
        estimatedTime = `${(estimatedTimeInSeconds / 3600).toFixed(0)} hour(s)`;
    }

    let summaryContainer = document.getElementById('summaryContainer');
    summaryContainer.innerHTML = `Summarizing... This may take approximately ${estimatedTime}`;
    summaryContainer.className = 'text-gray-500';

    fetch('/summarize', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            style: summaryStyle,
            content: text,  // 'text' is the data to summarize
        }),
    })
    .then(response => response.json())
    .then(data => {
        console.log(data);

        summaryContainer.innerHTML = data['summary'].replace(/\n/g, '<br>');
        summaryContainer.className = 'text-base font-normal text-gray-500 dark:text-white';
    })
    .catch(error => {
        // console.error('Error:', error);
        summaryContainer.innerHTML = "Error: " + error; 
    });
}

