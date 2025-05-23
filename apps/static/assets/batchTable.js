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

document.addEventListener('DOMContentLoaded', function() {
    updateBatchTable();  // update the table when the page loads
    setInterval(updateBatchTable, 60000);  // update the table every minute
  });