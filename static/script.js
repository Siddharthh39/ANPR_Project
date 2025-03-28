// Wait until the DOM is fully loaded
document.addEventListener("DOMContentLoaded", function() {
    const searchInput = document.getElementById("searchInput");
    if(searchInput) {
      searchInput.addEventListener("keyup", function() {
        const filter = searchInput.value.toLowerCase();
        const rows = document.querySelectorAll("#vehiclesTable tbody tr");
        rows.forEach((row) => {
          const cells = row.getElementsByTagName("td");
          let textContent = "";
          for(let i = 0; i < cells.length; i++) {
            textContent += cells[i].textContent.toLowerCase() + " ";
          }
          row.style.display = textContent.indexOf(filter) > -1 ? "" : "none";
        });
      });
    }
  });
  