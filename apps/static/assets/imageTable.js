    // import { Modal } from '/static/assets/flowbite.js';
    const defectClasses = {
      '1': { class: 'bg-emerald-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Alligator Crack' },
      '2': { class: 'bg-yellow-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Arrow' },
      '3': { class: 'bg-green-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Block Crack' },
      '4': { class: 'bg-blue-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Damaged Base Crack' },
      '5': { class: 'bg-indigo-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Localise Surface Defect' },
      '6': { class: 'bg-purple-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Multi Crack' },
      '7': { class: 'bg-pink-500 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Parallel Lines' },
      '8': { class: 'bg-red-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Peel Off With Cracks' },
      '9': { class: 'bg-emerald-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Peeling Off Premix' },
      '10': { class: 'bg-green-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Pothole With Crack' },
      '11': { class: 'bg-blue-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Rigid Pavement Crack' },
      '12': { class: 'bg-indigo-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Single Crack' },
      '13': { class: 'bg-purple-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Transverse Crack' },
      '14': { class: 'bg-pink-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Wearing Course Peeling Off' },
      '15': { class: 'bg-white text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'White Lane' },
      '16': { class: 'bg-amber-200 text-black text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Yellow Lane' }, 
      '17': { class: 'bg-green-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Raveling' },
      '18': { class: 'bg-blue-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Faded Kerb' },
      '19': { class: 'bg-indigo-700 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md', text: 'Paint Spillage' },
    };

    function getSeverityLabelAndColor(score) {
      if (score >= 4) {
        return { label: 'Very Severe', color: 'text-red-500 dark:text-red-400' };
      } else if (score === 3) {
        return { label: 'Severe', color: 'text-orange-500 dark:text-orange-400' };
      } else if (score === 2) {
        return { label: 'Normal', color: 'text-yellow-500 dark:text-yellow-400' };
      } else {
        return { label: 'Mild', color: 'text-green-500 dark:text-green-400' };
      }
    }


    function checktoggle(id){
      const toggle = document.getElementById(id);
    
        // Check if it's checked or not
        if (toggle.checked) {
            return true;
        } else {
            return false;
        }
    }
    
    function handleConfirmClick() {
      const insp_date = document.getElementById('insp_date').value;
      if (insp_date === '') {
        const today = new Date();
      
        const day = today.getDate();
        const month = today.getMonth() + 1; // January is 0
        const year = today.getFullYear();
        
        document.getElementById('insp_date').value = `${day}/${month}/${year}`;
      }
      
      tog1=checktoggle("toggle1");
      tog2=checktoggle("toggle2");
      tog3=checktoggle("toggle3");
      tog4=checktoggle("toggle4");
      tog5=checktoggle("toggle5");
      //add toggle 5 and 6 here
      tog=[tog1,tog2,tog3,tog4,tog5];
    
      var inspectionDate = document.getElementById('insp_date').value
      fetch('/start_process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            // Add any data you need to send in the body here
            total_frames: totalF,
            path: Fpath,
            user_id: '1',
            bid: bID,
            inspectionDate: inspectionDate,
            toggle:tog
        })
      })
      .then(response => {
          if (!response.ok) {
              throw  new Error('Network response was not ok');
          }
          return response.json();
      
    });

}

function handleClearAll() {
  document.getElementById('insp_date').value = "";
}

let selectedPath = "";  // Global variable to store the selected path filter
let selectedDefects = [];  // Global variable to store the selected defects filter

// function renderTableRows(filteredData) {
//   const tbody = document.querySelector('.imagetbody');
//   tbody.innerHTML = ''; // clear the table body
//   filteredData.sort((a, b) => a.imagePath.localeCompare(b.imagePath));
//   let rows = '';

//   filteredData.forEach((item, index) => {
//     const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
//     const defects = item.outputID.map((defect, index) => {
//       const defectKey = defect;
//       const defectClass = defectClasses[defectKey];
//       const severity = item.severity[index];
//       let concatBorder = '';
//       if (severity == 1) {
//         concatBorder = 'border-4 border-amber-400';
//       } else if (severity == 2) {
//         concatBorder = 'border-4 border-orange-500';
//       } else if (severity == 3) {
//         concatBorder = 'border-4 border-red-600';
//       }
//       if (!defectClass) {
//         console.error(`Defect not found: ${defectKey}`);
//         return `<span class="border-2 border-purple-600 bg-pink-600 text-white text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md">Unknown Defect</span>`;
//       }
//       return `<span class="${concatBorder} ${defectClass.class}">${defectClass.text}</span>`;
//     }).join(' ');

//     let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
//     b = b.replace(/(\.[\w\d_-]+)$/i, '_legend_defect$1');

//     const btnHTML = `<button id="report-${item.imageID}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">
//       View Report <svg class="w-4 h-4 ml-1 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
//     </button>`;

//     const row = `
//       <tr class="${rowClass}">
//         <td class="p-4 text-sm font-normal text-gray-900 whitespace-nowrap dark:text-white">${item.imagePath}</td>
//         <td class="p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white">${item.location}</td>
//         <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">${defects}</td>
//         <td class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">
//           <a id="view-${item.imageID}" href="${b}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">View</a>
//         </td>
//         <td class="p-4 whitespace-nowrap">
//           ${btnHTML}
//         </td>
//       </tr>
//     `;

//     rows += row;
//   });

//   tbody.innerHTML = rows;

//   // Reapply click events for buttons
//   filteredData.forEach((item) => {
//     document.getElementById(`report-${item.imageID}`).addEventListener('click', function(event) {
//       viewReport(event, item.imageID);
//     });
//   });
// }

function renderTableRows(filteredData) {
  const tbody = document.querySelector('.imagetbody');
  tbody.innerHTML = ''; // Clear the table body
  
  filteredData.sort((a, b) => a.imagePath.localeCompare(b.imagePath));

  let rows = '';

  filteredData.forEach((item, index) => {
    const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
    imagepath=item["imagePath"]
    console.log(item)
    // Only apply sorting if arrays are defined and of same length
    if (
      Array.isArray(item.defects) &&
      Array.isArray(item.outputID) &&
      Array.isArray(item.severity) &&
      Array.isArray(item.status) &&
      item.defects.length === item.outputID.length &&
      item.severity.length === item.outputID.length &&
      item.status.length === item.outputID.length
  ) {
      // Zip and sort by outputID
      const combined = item.outputID.map((id, i) => ({
          outputID: id,
          defect: item.defects[i],
          severity: item.severity[i],
          status: item.status[i]
      }));

      combined.sort((a, b) => a.outputID - b.outputID);

      // Unzip back into the item object
      item.outputID = combined.map(entry => entry.outputID);
      item.defects = combined.map(entry => entry.defect);
      item.severity = combined.map(entry => entry.severity);
      item.status = combined.map(entry => entry.status);
  }
    // Group defects by type
    const defectGroups = {};
    item.outputID.forEach((defectID, dIndex) => {
      const defectType = defectID;
      const severity = item.severity[dIndex];
      const defectstatus = item.status[dIndex] || "unchecked";

      console.log(item.status)

      if (!defectGroups[defectType]) {
        defectGroups[defectType] = { severity: [], count: 0, status: defectstatus };
      }
      
      
      defectGroups[defectType].severity.push(severity);
      defectGroups[defectType].count++;
      
    });
    // Create a row for each unique defect type
    Object.entries(defectGroups).forEach(([defectType, data], dIndex) => {
      const defectstatus = data.status;
      const defectClass = defectClasses[defectType] || { class: "border-purple-600 bg-pink-600 text-white", text: "Unknown Defect" };
      let severityBorder = '';
      // console.log(defectClasses[defectType])
      // console.log("defectclasses",defectClasses[defectType].text.replace(' ','_'))
      if (data.severity.includes(3)) {
        severityBorder = 'border-4 border-red-600';
      } else if (data.severity.includes(2)) {
        severityBorder = 'border-4 border-orange-500';
      } else if (data.severity.includes(1)) {
        severityBorder = 'border-4 border-amber-400';
      }
    
      const defectsHTML = `<span class="${severityBorder} ${defectClass.class}">${defectClass.text} (x${data.count})</span>`;
      const sanitizedDefect = defectClass.text.replace(/\s+/g, "-"); // Replace spaces with hyphens
      let b = '\\' + item.imagePath.split('\\').slice(item.imagePath.split('\\').indexOf('Batches')).join('\\');
      b = b.replace(/(\.[\w\d_-]+)$/i, '_legend_defect$1');
      imgpath=imagepath
      // console.log('imgpath:', imgpath);
      var defecttype=defectClasses[defectType].text
      // console.log("defecttype",defecttype)
      const btnID = `report-${item.imageID}-${sanitizedDefect}`;
      //KYUI THE BUTTONS HEREE
      // const btnHTML = `<a href='/makereport?imgpath=${encodeURIComponent(imgpath)}&defecttype=${encodeURIComponent(defecttype)}' id="${btnID}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">
      //   Make Report
      //   <svg class="w-4 h-4 ml-1 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
      //     <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
      //   </svg>
      // </a>`;
      console.log(item.imageID)
      let reportBtnHTML = '';
      let viewBtnHTML = '';
      console.log(defecttype,defectstatus,defectstatus[0] === "checked")
      if (defectstatus === "checked") {
        reportBtnHTML = `<a href='/makereport?imgpath=${encodeURIComponent(imgpath)}&defecttype=${encodeURIComponent(defecttype)}&status="checked' id="${btnID}" class="...">Edit Report</a>`;
        viewBtnHTML = `<a id="view-${item.imageID}" href="/viewreport?imageID=${item.imageID}&defecttype=${encodeURIComponent(defecttype)}" class="...">View Report</a>`;
      } else {
        reportBtnHTML = `<a href='/makereport?imgpath=${encodeURIComponent(imgpath)}&defecttype=${encodeURIComponent(defecttype)}&status="unchecked' id="${btnID}" class="...">Make Report</a>`;
        viewBtnHTML = `<a id="view-${item.imageID}" href="${b}" loading='lazy' class="...">View Image</a>`;
      }


      const row = `
        <tr class="${rowClass}">
          <td class="p-4 text-sm font-normal text-gray-900 whitespace-nowrap dark:text-white">${item.imagePath}</td>
          <td class="p-4 text-sm font-semibold text-gray-900 whitespace-nowrap dark:text-white">${item.location}</td>
          <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">${defectsHTML}</td>
          <td class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-white">
          ${viewBtnHTML}

          </td>
          <td class="p-4 whitespace-nowrap dark:text-white">
          ${reportBtnHTML}

          </td>
        </tr>
      `;
      //${btnHTML} <a id="view-${item.imageID}" href="${b}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">View Image</a>
      rows += row;
     
      // Attach event listener directly within the loop
      // setTimeout(() => {
      //   // document.addEventListener('DOMContentLoaded', () => {
      //   document.getElementById(btnID)?.addEventListener('click', function (event) {
      //     // console.log(defectType)
      //     // window.location.href = "{{ url_for('makereport', imgpath='imgpath') }}";
      //     // window.location.href = "/makereport?imgpath=${encodeURIComponent(imgpath)}"
      //     window.location.href = `/makereport?imgpath=${encodeURIComponent(imgpath)}&defecttype=${encodeURIComponent(defecttype)}`;

      //     // viewReport(event, item.imageID, defectType); // Pass defectType as the identifier/batch/${batchID}
      //     // fetch(`/makereport`, {
      //     //   method: 'POST', // Using POST method to send data
      //     //   headers: {
      //     //     'Content-Type': 'application/json',
      //     //   },
      //     //   body: JSON.stringify({
      //     //     imagepath: imgpath,
      //     //   }),
      //     //   })
      //     //   .then(
      //     //   response => response.json()
      //     //   )
      //     //   .then(data => {});
      //   });
      // // })
      // }, 0);
    });
  });

  tbody.innerHTML = rows;
}

function filterTableByImagePath(data, selectedPath) {
  return data.filter(item => {
    const partOfPath = item.imagePath.split('\\').slice(-2, -1)[0];
    return partOfPath === selectedPath;
  });
}

function filterTableByDefects(data) {
  return data.filter(item => {
    const defectsInRow = item.outputID.map(defect => {
      return defectClasses[defect].text.trim().toLowerCase().replace(/\s/g, '-');
    });

    return selectedDefects.every(defect => defectsInRow.includes(defect)) || selectedDefects.length === 0;
  });
}

function updateFilterOptions(data) {
  const uniquePartOfPaths = new Set();
  
  data.forEach(item => {
    const partOfPath = item.imagePath.split('\\').slice(-2, -1)[0];
    uniquePartOfPaths.add(partOfPath);
  });

  const filterDropdown = document.getElementById('imagePathFilter');
  filterDropdown.innerHTML = '';

  const firstOption = document.createElement('option');
  firstOption.disabled = true;
  firstOption.selected = true;
  firstOption.value = "";
  firstOption.style.color = "white";
  firstOption.text = "Video";
  filterDropdown.appendChild(firstOption);

  const uniquePathsArray = Array.from(uniquePartOfPaths);

  uniquePathsArray.forEach((partOfPath, index) => {
    const option = document.createElement('option');
    option.value = partOfPath;
    option.text = partOfPath;
    option.style.color = "white";
    
    filterDropdown.appendChild(option);

    // Set the selectedPath to the first valid option if not already set
    if (!selectedPath && index === 0) {
      selectedPath = partOfPath;
    }
  });

  // Set the dropdown to the selectedPath if it's not already set
  if (selectedPath) {
    filterDropdown.value = selectedPath;
  }
}

function applyFilters(data) {
  let filteredData = filterTableByImagePath(data, selectedPath);
  filteredData = filterTableByDefects(filteredData);
  renderTableRows(filteredData);
}

function updateImageTable() {
  var path = window.location.pathname;
  var batchid = path.split('/')[2];
  if ((path == "/") || (path == "/index")){
      batchid = bID;
  }

  fetch(`/update_image_table/${batchid}`)
    .then(response => response.json())
    .then(data => {
      updateFilterOptions(data);
      applyFilters(data);
      
      document.getElementById('imagePathFilter').addEventListener('change', function() {
        selectedPath = this.value;  // Update the global filter value
        applyFilters(data);
      });

      const defectCheckboxes = document.querySelectorAll('#dropdown2 input[type="checkbox"]');
      defectCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
          selectedDefects = Array.from(defectCheckboxes)
            .filter(checkbox => checkbox.checked)
            .map(checkbox => checkbox.value);  // Update the global defects filter
          applyFilters(data);
        });
      });
    });
}

document.addEventListener('DOMContentLoaded', function() {
  updateImageTable();  // update the table when the page loads
  setInterval(updateImageTable, 5000);  // update the table every 5 seconds
});


function viewReport(event, imageID, defect) {

fetch(`/get_reportPath/${imageID}/${defect}`)
  .then(response => response.json())
  .then(data => {
    console.log('Report data:', data);
    fetch('/view_temp', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify({
          path: data['reportPath'],
      }),
    });
    })
  }

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






