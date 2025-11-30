function uploadFile() {
  const form = document.getElementById('upload-form');
  //const formData = new FormData(form);
  const input_file = document.getElementById('file-input');
  const input_img = document.getElementById('img-input');
  const input_text = document.getElementById('text-input');

  const formData = new FormData();
  formData.append('video', input_file.files[0]);
  formData.append('img', input_img.files[0]);
  formData.append('text', input_text.value);

  fetch('/api/upload', {
    method: 'POST',
    body: formData
  })
  .then(response => response.json())
  .then(data => console.log('Success:', data))
  .catch(error => console.error('Error:', error));
}