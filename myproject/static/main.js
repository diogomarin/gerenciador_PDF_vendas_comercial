document.getElementById('uploadForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    let formData = new FormData();
    let fileField = document.getElementById('pdfFile');
    
    formData.append('file', fileField.files[0]);
    
    fetch('/upload_pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let messageDiv = document.getElementById('message');
        if (data.error) {
            messageDiv.innerText = 'Error: ' + data.error;
        } else {
            messageDiv.innerText = 'Success: ' + data.message;
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
});
