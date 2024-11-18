document.addEventListener('DOMContentLoaded', function() {
  const dropzoneFileInput = document.getElementById('dropzone-file');
  const videoPlayer = document.getElementById('video-player');
  const dropzone = dropzoneFileInput.parentNode;
  const toggleSwitch = document.getElementById('dropbox-toggle'); // Assuming you have a toggle switch with this ID
  
  // Prevent default drag behaviors
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, preventDefaults, false)
    document.body.addEventListener(eventName, preventDefaults, false)
  });

  function preventDefaults(e) {
    e.preventDefault()
    e.stopPropagation()
  }

  // Highlight drop area when item is dragged over it
  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, highlight, false)
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, unhighlight, false)
  });

  function highlight() {
    dropzone.classList.add('highlight')
  }

  function unhighlight() {
    dropzone.classList.remove('highlight')
  }

  dropzone.addEventListener('drop', handleDrop, false);

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    handleFiles(files);
  }
  
  function handleFiles(files) {
    Array.from(files).forEach(file => {
      Fpath = file.name;
      if (file.type.startsWith('video/')) {
        const reader = new FileReader();

        reader.onload = function(e) {
          videoPlayer.src = e.target.result;
          videoPlayer.classList.remove('hidden');
          videoPlayer.classList.add('block');

          // Hide the dropzone
          dropzone.classList.add('hidden');
        };

        reader.readAsDataURL(file);
      } else {
          const uploadMessage = document.getElementById('upload-message');
          uploadMessage.textContent = `Folder: "${file.name}" uploaded`;
          uploadMessage.classList.remove('hidden');
        
          // Grey out the dropzone
          const dropzone = document.getElementById('dropzone');
          dropzone.style.display = 'none';
          fetch(`/get_total_frames?folder=${encodeURIComponent(file.name)}`)
          .then(response => response.json())
          .then(data => {
              Fpath=file.name
              totalF = data.totalF;
              updateElements();
          })
          .catch(error => console.error('Error:', error));
                  }
    });

    videoPlayer.onloadedmetadata = function() {
      totalF += Math.floor(videoPlayer.duration);
      updateElements();       
      console.log('Video length in seconds: ' + videoPlayer.duration);
      console.log('Total length of all videos: ' + totalF);
    };
  }

  dropzoneFileInput.addEventListener('change', function(event) {
    const files = event.target.files;
    handleFiles(files);
  });
  
  // Update dropzone click behavior based on toggle switch
  dropzone.addEventListener('click', function() {
    if (toggleSwitch.checked) {
      // Use Dropbox chooser
      Dropbox.choose({
        success: function(files) {
          console.log(files);
                var sharedLink = files[0].link;
                var name =  files[0].name;
                var isFolder = files[0].isDir;
                var id = files[0].id;
                fetch('/download', {
                  method: 'POST',
                  headers: {
                      'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({ dropbox_path: sharedLink, name: name, id: id, is_folder: isFolder})
              })
              .then(response => response.json())
              .then(data => {
                  if (data.error) {
                      console.error('Error downloading file:', data.error);
                  } else {
                      alert('File downloaded successfully');
                      Fpath = name;
                      if (isFolder) {
                          const uploadMessage = document.getElementById('upload-message');
                          uploadMessage.textContent = `Folder: "${name}" uploaded`;
                          uploadMessage.classList.remove('hidden');
                        
                          // Grey out the dropzone
                          const dropzone = document.getElementById('dropzone');
                        dropzone.style.display = 'none';
                          fetch(`/get_total_frames?folder=${encodeURIComponent(name)}`)
                          .then(response => response.json())
                          .then(data => {
                              totalF = data.totalF;
                              updateElements();
                          })
                          .catch(error => console.error('Error:', error));
                      } else {
                      videoPlayer.src = sharedLink.replace('&dl=0', '&raw=1');
                      videoPlayer.classList.remove('hidden');
                      videoPlayer.classList.add('block');

                      // Hide the dropzone
                      dropzone.classList.add('hidden');

                      videoPlayer.onloadedmetadata = function() {
                          totalF += Math.floor(videoPlayer.duration);
                          updateElements();
                          console.log('Video length in seconds: ' + videoPlayer.duration);
                          console.log('Total length of all videos: ' + totalF);
                      };
                    }
                  }
              })
              .catch(error => console.error('Error:', error));
         },
        folderselect: true,
        multiselect: false,
        extensions: ['.mp4', '.jpg', '.jpeg', '.png', '.gif', '.webm', '.mov', '.avi', '.mkv'],
      });
    } else {

    }
  });
});          
// const folderUrl = files[0].link;
// document.getElementById('folder-url').value = folderUrl;
// document.getElementById('download-form').submit();
// console.log(folderUrl)
// console.log(files)