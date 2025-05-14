// Select all checkboxes in the toggle group
const checkboxes = document.querySelectorAll('.toggle-group input[type="checkbox"]');

// Add event listeners to all checkboxes
checkboxes.forEach(checkbox => {
  checkbox.addEventListener('change', () => {
    // Check if all checkboxes are unchecked
    const noneChecked = [...checkboxes].every(cb => !cb.checked);

    // Prevent unchecking the last checkbox
    if (noneChecked) {
      checkbox.checked = true;
      alert("At least one AI must be on to be able to predict anything.");
    }
  });
});
