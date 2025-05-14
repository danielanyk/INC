document.addEventListener('DOMContentLoaded', function () {
  document.getElementById('reportdetails').addEventListener('submit', async function (e) {
    e.preventDefault();
    console.log(document.getElementById('defecttype').value)
    const repeatYes = document.getElementById("repeat-yes");
    const repeatNo = document.getElementById("repeat-no");

    let defectRepeatedValue = "";
    if (repeatYes.checked) {
      defectRepeatedValue = repeatYes.value; // "Yes"
    } else if (repeatNo.checked) {
      defectRepeatedValue = repeatNo.value; // "No"
    }
    
    const formData = {
      defectRepeatedValue:defectRepeatedValue,
      defectimg: document.getElementById('defectimg').value,
      defecttype: document.getElementById('defecttype').value,
      imgpath: document.getElementById('imgpath').value,
      inspectedBy: document.getElementById('inspection-officer').value,
      inspectionDate: document.getElementById('inspection-date').value,
      defectnumber: document.getElementById('defect-ref-no').value,
      quantity: document.getElementById('quantity').value,
      measurement: document.getElementById('measurement').value,
      cause: document.getElementById('defectCause').value,
      recommendation: document.getElementById('recommendation').value,
      remarks: document.getElementById('remarks').value,
      supervisor: document.getElementById('supervising-officer').value,
      via: "",
      acknowledgement: "",
      defectstatus: document.getElementById('status').value
    };
    
    try {
      const response = await fetch('/submit_report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const result = await response.json();
      alert(result.message || 'Form submitted!');
      window.history.back();
    } catch (err) {
      alert('Error submitting form');
      console.error(err);
    }
  });
});
