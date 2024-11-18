// instead of starting process with the start process button, start process button using the confirm button in modal
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('start_video_process').addEventListener('click', () => {
        console.log("start process button clicked");
    });
});


document.addEventListener('DOMContentLoaded', (event) => {
    const shutdownButton = document.querySelector('button[type="button"].bg-red-700');
    
    if (shutdownButton) {
        shutdownButton.addEventListener('click', () => {
            fetch('/shutdown', {
                method: 'POST'
            })
            .then(response => {
                if (response.ok) {
                    alert('Shutdown initiated successfully.');
                } else {
                    alert('Failed to initiate shutdown.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred while initiating shutdown.');
            });
        });
    }
});