// --- Helper Functions ---
  function getSelectedStatuses() {
    const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="status-"]');
    const selected = [];
    checkboxes.forEach(cb => {
      if (cb.checked) selected.push(cb.value.toLowerCase());
    });
    return selected;
  }

  function getSelectedDateRange() {
    const startDate = document.getElementById("start-date").value;
    const endDate = document.getElementById("end-date").value;
    return { startDate, endDate };
  }

  function toDateOnlyString(dateStr) {
  const d = new Date(dateStr);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
  }

  function formatDate(date) {
    return date.toISOString().split('T')[0];
  }

  function getDateRange(option) {
    const today = new Date();
    let start, end;

    switch (option.toLowerCase()) {
      case 'yesterday':
        start = new Date(today);
        start.setDate(today.getDate() - 1);
        end = start;
        break;
      case 'today':
        start = end = today;
        break;
      case 'last 7 days':
        end = today;
        start = new Date(today);
        start.setDate(today.getDate() - 6);
        break;
      case 'last 30 days':
        end = today;
        start = new Date(today);
        start.setDate(today.getDate() - 29);
        break;
      case 'last 90 days':
        end = today;
        start = new Date(today);
        start.setDate(today.getDate() - 89);
        break;
      case 'custom...':
        start = end = null;
        break;
      default:
        start = end = null;
    }
    return { start, end };
  }

  // function updateBatchTable() {
  //   const statusClasses = {
  //     'in progress': { class: 'bg-purple-100 text-purple-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-purple-100 dark:bg-gray-700 dark:border-purple-500 dark:text-purple-400', text: 'In Progress' },
  //     'completed': { class: 'bg-green-100 text-green-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md dark:bg-gray-700 dark:text-green-400 border border-green-100 dark:border-green-500', text: 'Completed' },
  //     'error': { class: 'bg-red-100 text-red-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-red-100 dark:bg-gray-700 dark:border-red-500 dark:text-red-400', text: 'Error' },
  //     'paused': { class: 'bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-blue-100 dark:bg-gray-700 dark:border-blue-500 dark:text-blue-400', text: 'Paused' },
  //     'inferencing': { class: 'bg-yellow-100 text-yellow-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-yellow-100 dark:bg-gray-700 dark:border-yellow-500 dark:text-yellow-400', text: 'Inferencing' },
  //     'splitting': { class: 'bg-orange-100 text-orange-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-orange-100 dark:bg-gray-700 dark:border-orange-500 dark:text-orange-400', text: 'Splitting' },
  //     'pre-processing': { class: 'bg-teal-100 text-teal-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-teal-100 dark:bg-gray-700 dark:border-teal-500 dark:text-teal-400', text: 'Pre-Processing' }
  //   };

  //   const selectedStatuses = getSelectedStatuses();
  //   const { startDate, endDate } = getSelectedDateRange();

  //   fetch('/update_batch_table')
  //     .then(response => response.json())
  //     .then(data => {
  //       const tbody = document.querySelector('.batchtbody');
  //       tbody.innerHTML = '';

  //       let filteredData = data;

  //       if (selectedStatuses.length !== 0) {
  //         filteredData = filteredData.filter(item => selectedStatuses.includes(item.status.toLowerCase()));
  //       }

  //       if (startDate) {
  //         const startDateOnly = toDateOnlyString(startDate);
  //         filteredData = filteredData.filter(item => toDateOnlyString(item.batchStartProcessing) >= startDateOnly);
  //       }

  //       if (endDate) {
  //         const endDateOnly = toDateOnlyString(endDate);
  //         filteredData = filteredData.filter(item => toDateOnlyString(item.batchStartProcessing) <= endDateOnly);
  //       }

  //       filteredData.forEach((item, index) => {
  //         const status = statusClasses[item.status.toLowerCase()] || { class: '', text: item.status };
  //         const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';

  //         const row = `
  //           <tr class="${rowClass}">
  //             <td class="p-4 text-sm text-gray-500 dark:text-white">Started By <span class="font-semibold">${item.displayname}</span></td>
  //             <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">${item.batchStartProcessing}</td>
  //             <td class="p-4 text-sm text-gray-500 dark:text-white">${item.totalFrames}</td>
  //             <td class="p-4 text-sm text-gray-500 dark:text-white">${item.batchPath}</td>
  //             <td class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">
  //               <a href="/batch/${item.batchID}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">
  //                 View
  //               </a>
  //             </td>
  //             <td class="p-4 whitespace-nowrap">
  //               <span class="${status.class}">${status.text}</span>
  //             </td> 
  //           </tr>
  //         `;
  //         tbody.innerHTML += row;
  //       });
  //     });
  // }


// function updateBatchTable() {
//     const statusClasses = {
//   'in progress': { class: 'bg-purple-100 text-purple-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-purple-100 dark:bg-gray-700 dark:border-purple-500 dark:text-purple-400', text: 'In Progress' },
//   'completed': { class: 'bg-green-100 text-green-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md dark:bg-gray-700 dark:text-green-400 border border-green-100 dark:border-green-500', text: 'Completed' },
//   'error': { class: 'bg-red-100 text-red-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-red-100 dark:bg-gray-700 dark:border-red-500 dark:text-red-400', text: 'Error' },
//   'paused': { class: 'bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-blue-100 dark:bg-gray-700 dark:border-blue-500 dark:text-blue-400', text: 'Paused' },
//   'inferencing': { class: 'bg-yellow-100 text-yellow-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-yellow-100 dark:bg-gray-700 dark:border-yellow-500 dark:text-yellow-400', text: 'Inferencing' },
//   'splitting': { class: 'bg-orange-100 text-orange-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-orange-100 dark:bg-gray-700 dark:border-orange-500 dark:text-orange-400', text: 'Splitting' },
//   'pre-processing': { class: 'bg-teal-100 text-teal-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-teal-100 dark:bg-gray-700 dark:border-teal-500 dark:text-teal-400', text: 'Pre-Processing' }
//     };
  
//     fetch('/update_batch_table')  // replace with your Flask route
//       .then(response => response.json())
//       .then(data => {
//         const tbody = document.querySelector('.batchtbody');  // select the table body by class name
//         tbody.innerHTML = '';  // clear the table body
  
//         // loop through the data and append rows to the table body
//         data.forEach((item, index) => {
//           const status = statusClasses[item.status.toLowerCase()] || { class: '', text: item.status };
//           const rowClass = (index+1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';
  
//           const row = `
//             <tr class="${rowClass}">
//               <td class="p-4 text-sm text-gray-500 dark:text-white">Started By <span class="font-semibold">${item.displayname}</td></span>
//               <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">${item.batchStartProcessing}</td>
//               <td class="p-4 text-sm text-gray-500 dark:text-white">${item.totalFrames}</td>
//               <td class="p-4 text-sm text-gray-500 dark:text-white">${item.batchPath}</td>
//               <td
//               class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">
//               <a href="/batch/${item.batchID}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">View
//               </a>
//               </td>
//               <td class="p-4 whitespace-nowrap">
//               <span class="${status.class}">${status.text}</span>
//               </td>
//             </tr>
//           `;
//           tbody.innerHTML += row;
//         });
//       });
//   }
function updateBatchTable() {
  const statusClasses = {
    'in progress': { class: 'bg-purple-100 text-purple-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-purple-100 dark:bg-gray-700 dark:border-purple-500 dark:text-purple-400', text: 'In Progress' },
    'completed': { class: 'bg-green-100 text-green-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md dark:bg-gray-700 dark:text-green-400 border border-green-100 dark:border-green-500', text: 'Completed' },
    'error': { class: 'bg-red-100 text-red-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-red-100 dark:bg-gray-700 dark:border-red-500 dark:text-red-400', text: 'Error' },
    'paused': { class: 'bg-blue-100 text-blue-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-blue-100 dark:bg-gray-700 dark:border-blue-500 dark:text-blue-400', text: 'Paused' },
    'inferencing': { class: 'bg-yellow-100 text-yellow-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-yellow-100 dark:bg-gray-700 dark:border-yellow-500 dark:text-yellow-400', text: 'Inferencing' },
    'splitting': { class: 'bg-orange-100 text-orange-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-orange-100 dark:bg-gray-700 dark:border-orange-500 dark:text-orange-400', text: 'Splitting' },
    'pre-processing': { class: 'bg-teal-100 text-teal-800 text-xs font-medium mr-2 px-2.5 py-0.5 rounded-md border border-teal-100 dark:bg-gray-700 dark:border-teal-500 dark:text-teal-400', text: 'Pre-Processing' }
  };

  const userID = localStorage.getItem('userid'); // Get userid from localStorage

  // Use it as a query parameter
  fetch(`/update_batch_table?userid=${encodeURIComponent(userID)}`)
    .then(response => response.json())
    .then(data => {
      const tbody = document.querySelector('.batchtbody');
      tbody.innerHTML = '';
      // <td class="p-4 text-sm text-gray-500 dark:text-white">${item.totalFrames}</td>
      data.forEach((item, index) => {
        const status = statusClasses[item.processingstatus.toLowerCase()] || { class: '', text: item.processingstatus };
        const rowClass = (index + 1) % 2 === 0 ? 'bg-gray-50 dark:bg-gray-700' : '';

        const row = `
          <tr class="${rowClass}">
            <td class="p-4 text-sm text-gray-500 dark:text-white">Started By <span class="font-semibold">${item.username}</span></td>
            <td class="p-4 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">${item.uploaddatetime}</td>
             
            <td class="p-4 text-sm text-gray-500 dark:text-white">${item.foldername}</td>
            <td class="inline-flex items-center p-4 space-x-2 text-sm font-normal text-gray-500 whitespace-nowrap dark:text-gray-400">
              <a href="/batch/${item.videoid}" class="inline-flex items-center p-2 text-xs font-medium uppercase rounded-lg text-primary-700 sm:text-sm hover:bg-gray-100 dark:text-primary-500 dark:hover:bg-gray-700">View</a>
            </td>
            <td class="p-4 whitespace-nowrap">
              <span class="${status.class}">${status.text}</span>
            </td>
          </tr>
        `;
        tbody.innerHTML += row;
      });
    });
}

  // --- DOM Ready ---
document.addEventListener('DOMContentLoaded', () => {
  const dropdownButton = document.getElementById('dropdownButton');
  const dropdownMenu = document.getElementById('transactions-dropdown');
  const dropdownLabel = document.getElementById('dropdown-label');
  const dateInputs = {
    start: document.getElementById('start-date'),
    end: document.getElementById('end-date')
  };

  // Initial table load
  updateBatchTable();
  setInterval(updateBatchTable, 60000); // Auto-refresh every 60s

  // Status checkbox event listeners
  const statusCheckboxes = document.querySelectorAll('input[type="checkbox"][id^="status-"]');
  statusCheckboxes.forEach(cb => cb.addEventListener('change', updateBatchTable));

  // ✅ Proper datepicker event listeners (Flowbite)
  ['start', 'end'].forEach(key => {
    dateInputs[key].addEventListener('changeDate', updateBatchTable); // Flowbite-specific
    dateInputs[key].addEventListener('input', updateBatchTable);      // fallback if typing manually
  });

  // Toggle dropdown menu
  dropdownButton.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdownMenu.classList.toggle('hidden');
  });

  // Handle dropdown selection
  dropdownMenu.querySelectorAll('.dropdown-option').forEach(optionEl => {
    optionEl.addEventListener('click', (e) => {
      e.preventDefault();
      const selectedText = optionEl.textContent.trim();
      dropdownLabel.textContent = selectedText;

      const { start, end } = getDateRange(selectedText);
      if (start && end) {
        dateInputs.start.value = formatDate(start);
        dateInputs.end.value = formatDate(end);

        // Trigger update manually since 'changeDate' won’t fire for direct .value changes
        updateBatchTable();
      } else if (selectedText.toLowerCase() === 'custom...') {
        dateInputs.start.value = '';
        dateInputs.end.value = '';
        // Optional: show calendar UI if needed
        updateBatchTable();
      }

      dropdownMenu.classList.add('hidden');
    });
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', () => {
    dropdownMenu.classList.add('hidden');
  });
});
