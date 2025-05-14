// import { Modal } from '/static/assets/flowbite.js';

// To be added as a new file in static/assets

const defectClasses = {
  'alligator crack': { class: 'bg-red-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Alligator Crack' },
  'arrow': { class: 'bg-yellow-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Arrow' },
  'block crack': { class: 'bg-green-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Block Crack' },
  'damaged base crack': { class: 'bg-blue-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Damaged Base Crack' },
  'localise surface defect': { class: 'bg-indigo-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Localise Surface Defect' },
  'multi crack': { class: 'bg-purple-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Multi Crack' },
  'parallel lines': { class: 'bg-pink-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Parallel Lines' },
  'peel off with cracks': { class: 'bg-red-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Peel Off With Cracks' },
  'peeling off premix': { class: 'bg-yellow-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Peeling Off Premix' },
  'pothole with crack': { class: 'bg-green-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Pothole With Crack' },
  'rigid pavement crack': { class: 'bg-blue-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Rigid Pavement Crack' },
  'single crack': { class: 'bg-indigo-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Single Crack' },
  'transverse crack': { class: 'bg-purple-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Transverse Crack' },
  'wearing course peeling off': { class: 'bg-pink-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Wearing Course Peeling Off' },
  'white lane': { class: 'bg-red-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'White Lane' },
  'yellow lane': { class: 'bg-yellow-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Yellow Lane' },
  'raveling': { class: 'bg-green-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Raveling' },
  'damaged kerb': { class: 'bg-blue-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Damaged Kerb' },
  'paint spillage': { class: 'bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label', text: 'Paint Spillage' },
};

// function getFilterValues() {
//       return new Promise((resolve) => {
//         document.addEventListener('DOMContentLoaded', function() {
//           const selectedDefect = document.querySelector('#defectDropdown').value || 'defaultDefect';
//           const startDate = document.querySelector('#startDate').value || 'defaultStartDate';
//           const endDate = document.querySelector('#endDate').value || 'defaultEndDate';
//           resolve({ selectedDefect, startDate, endDate });
//         });
//       });
//     }

function populateDefectDropdown() {
const dropdownContent = document.querySelector('.dropdown-content'); // Select the dropdown content container
const defects = Object.keys(defectClasses); // Get keys from the defectClasses object

// Clear existing options first
dropdownContent.innerHTML = ''; // Clear existing checkboxes

// Iterate over defects to create and append checkbox elements
defects.forEach(defect => {
const div = document.createElement('div');
const checkbox = document.createElement('input');
checkbox.type = 'checkbox';
checkbox.id = defect;
checkbox.value = defect;
const label = document.createElement('label');
label.htmlFor = defect;
label.textContent = defect.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()); // Format the defect text

div.appendChild(checkbox);
div.appendChild(label);
dropdownContent.appendChild(div);
});
}

function processItem(b, b_defects, rowClass, defects, item) {
let b_sliced = b.slice(9);

// Create the checkbox
var checkbox = document.createElement("input");
checkbox.type = "checkbox";
checkbox.id = `select-${item.imageID}`;
checkbox.className = "form-checkbox h-5 w-5 text-gray-600";

// Convert the checkbox to an HTML string
var checkboxHTML = checkbox.outerHTML;

// Replace checkFileExists with direct fetch call
return fetch(`/check_file_exists?filePath=${encodeURIComponent(b_defects)}`)
  .then(response => response.json())
  .then(data => {
      const exists = data.exists;
      const href = exists ? b_defects : b;
return `
  <tr class="${rowClass}">
    <td class="p-4 text-sm font-normal text-gray-900 whitespace-nowrap dark:text-white batch-number">${item.batchID}</td>
    <td class="p-4 text-sm font-normal text-gray-900 whitespace-nowrap dark:text-white frame-name">${b_sliced}</td>
    <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400 defects">${defects}</td>
    <td class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">
      <a href="${href}" target="_blank" rel="noopener noreferrer" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">View Image</a>
    </td>
    <td class="p-4 whitespace-nowrap text-center align-middle">
      ${checkboxHTML}
    </td>
  </tr>
`;
});
}

function updateEditorTable() {
fetch(`/update_editor_table`)
.then(
  response => response.json()
)
.then(data => {
  const tbody = document.querySelector('.imagetbody');  // select the table body by class name
  tbody.innerHTML = '';  // clear the table body
  // loop through the data and append rows to the table body
  const fetchPromises = data.map((item, index) => {
    const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
    const defects = item.defects.map(defect => {
      const outputLabel = defect['outputLabel'].toLowerCase();
      const defectClass = defectClasses[outputLabel];
    
      if (!defectClass) {
        console.log(`No class found for outputLabel: ${outputLabel}`);
        return `<span class="bg-slate-950 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label">${defect['outputLabel']}
                  <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
                </span>`;
      }
    
      // Include bbox as a hidden element
      return `<span class="${defectClass.class}">${defectClass.text}
                <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
              </span>`;
    }).join(' ');
    let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
    let b_defects = b.replace(/(\.[\w\d_-]+)$/i, '_defect$1');
    
    return processItem(b, b_defects, rowClass, defects, item);
  });
  
  Promise.all(fetchPromises).then(rows => {
    tbody.innerHTML = rows.join('');
  });
});
}

function filterEditorTable(startDate, endDate, defectList) {
fetch(`/filter_editor_table`, {
method: 'POST', // Using POST method to send data
headers: {
  'Content-Type': 'application/json',
},
body: JSON.stringify({
  startDate: startDate,
  endDate: endDate,
  defectList: defectList,
}),
})
.then(
response => response.json()
)
.then(data => {
console.log(data)
const tbody = document.querySelector('.imagetbody');  // select the table body by class name
tbody.innerHTML = '';  // clear the table body
// loop through the data and append rows to the table body
const fetchPromises = data.map((item, index) => {
  const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
  const defects = item.defects.map(defect => {
    const outputLabel = defect['outputLabel'].toLowerCase();
    const defectClass = defectClasses[outputLabel];
  
    if (!defectClass) {
      console.log(`No class found for outputLabel: ${outputLabel}`);
      return `<span class="bg-slate-950 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label">${defect['outputLabel']}
                <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
              </span>`;
    }
  
    // Include bbox as a hidden element
    return `<span class="${defectClass.class}">${defectClass.text}
              <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
            </span>`;
  }).join(' ');
  let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
  let b_defects = b.replace(/(\.[\w\d_-]+)$/i, '_defect$1');
  
  return processItem(b, b_defects, rowClass, defects, item);
});

Promise.all(fetchPromises).then(rows => {
  tbody.innerHTML = rows.join('');
});
});
}

function loadMoreImages() {
const tableRows = document.querySelectorAll('#batchImage-table tr');
const startIndex = tableRows.length;
const endIndex = startIndex + 30;
fetch('/load_more_images', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ startindex: startIndex, endindex: endIndex }),
})
.then(response => response.json())
.then(data => {
  const tbody = document.querySelector('.imagetbody'); // select the table body by class name
  // loop through the data and append rows to the table body
  const fetchPromises = data.map((item, index) => {
    const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
    const defects = item.defects.map(defect => {
      const outputLabel = defect['outputLabel'].toLowerCase();
      const defectClass = defectClasses[outputLabel];
    
      if (!defectClass) {
        console.log(`No class found for outputLabel: ${outputLabel}`);
        return `<span class="bg-slate-950 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label">${defect['outputLabel']}
                  <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
                </span>`;
      }
      // Include bbox as a hidden element
      return `<span class="${defectClass.class}">${defectClass.text}
                <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
              </span>`;
    }).join(' ');
    let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
    let b_defects = b.replace(/(\.[\w\d_-]+)$/i, '_defect$1');
    
    return processItem(b, b_defects, rowClass, defects, item);
  });
  
  Promise.all(fetchPromises).then(rows => {
    tbody.innerHTML += rows.join('');
  });
});
}

function loadMoreFilteredImages(startDate, endDate, defectList) {
const tableRows = document.querySelectorAll('#batchImage-table tr');
const startIndex = tableRows.length;
const endIndex = startIndex + 30;
fetch('/load_more_filtered_images', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({ startDate: startDate, endDate: endDate, defectList: defectList, startindex: startIndex, endindex: endIndex }),
})
.then(response => response.json())
.then(data => {
  const tbody = document.querySelector('.imagetbody'); // select the table body by class name
  // loop through the data and append rows to the table body
  const fetchPromises = data.map((item, index) => {
    const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
    const defects = item.defects.map(defect => {
      const outputLabel = defect['outputLabel'].toLowerCase();
      const defectClass = defectClasses[outputLabel];
    
      if (!defectClass) {
        console.log(`No class found for outputLabel: ${outputLabel}`);
        return `<span class="bg-slate-950 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md label">${defect['outputLabel']}
                  <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
                </span>`;
      }
    
      // Include bbox as a hidden element
      return `<span class="${defectClass.class}">${defectClass.text}
                <span class="hidden bbox" data-label="${defect['outputLabel']}">${defect['bbox']}</span>
              </span>`;
    }).join(' ');
    let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
    let b_defects = b.replace(/(\.[\w\d_-]+)$/i, '_defect$1');
    
    return processItem(b, b_defects, rowClass, defects, item);
  });
  
  Promise.all(fetchPromises).then(rows => {
    tbody.innerHTML += rows.join('');
  });
});
}

let filterButtonPressed = false; // Declare a flag variable
document.addEventListener('DOMContentLoaded', function() {
let currentStartDate = '';
let currentEndDate = '';
let currentDefectList = [];
// var modal = new Modal(document.getElementById("default-modal"));
populateDefectDropdown();
const dropdownBtn = document.getElementById('dropdown-btn');
const dropdownContent = document.getElementById('dropdown-content');

dropdownBtn.addEventListener('click', function() {
// Toggle dropdown visibility
if (dropdownContent.classList.contains('hidden')) {
  dropdownContent.classList.remove('hidden');
} else {
  dropdownContent.classList.add('hidden');
}
});
updateEditorTable();  // update the table when the page loads
loadMoreImages(); // load more images to table when the button is clicked
setInterval(updateEditorTable, 1800000);  // Update the table every 30 minutes

document.getElementById('filterButton').addEventListener('click', function () {
filterButtonPressed = true; // Set the flag to true when the button is clicked

// Get the values of inputs with the ids startDate and endDate
const startDate = document.getElementById('startDate').value;
const endDate = document.getElementById('endDate').value;
let defectList = [];
// console.log('Start Date:', startDate, 'End Date:', endDate);

// Get the value of an input of type checkbox within a div that is within a div with the id/class 'dropdown-content'
document.querySelectorAll('.dropdown-content div input[type="checkbox"]').forEach(checkbox => {
  if (checkbox.checked) {
    // If checkbox.value is not alligator crack, capitalize the first letter of each word
    if (checkbox.value !== 'alligator crack') {
      defectList.push(checkbox.value.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()));
    } else {
    defectList.push(checkbox.value);
    }
  }
});

currentStartDate = startDate;
currentEndDate = endDate;
currentDefectList = defectList;

filterEditorTable(startDate, endDate, defectList);
});

document.getElementById('loadMore').addEventListener('click', function() {
  if (filterButtonPressed) {
    loadMoreFilteredImages(currentStartDate, currentEndDate, currentDefectList); // load more images to table when the button is clicked
  } else {
    loadMoreImages(); // load more images to table when the button is clicked
  }

});
});


// // Get the modal image tag
// var modalImg = document.getElementById("modal-img");

// // This function is called when a small image is clicked
// function showModal(src) {
//   modal.show()
//   modalImg.src = src;
//   m
// }

// // This function is called when the close button is clicked
// function closeModal() {
//   modal.classList.add('hidden');
// }
