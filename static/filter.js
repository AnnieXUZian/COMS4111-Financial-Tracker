function filterTransactions() {
    // Get date range values
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;

    // Convert input dates to Date objects for comparison
    const start = new Date(startDate);
    const end = new Date(endDate);

    // Get all transaction rows
    const rows = document.querySelectorAll('#transaction-table tbody tr');

    rows.forEach(row => {
        // Get the transaction date from the data-date attribute
        const transactionDate = new Date(row.getAttribute('data-date'));

        // Check if the transaction date is within the selected range
        if ((!startDate || transactionDate >= start) && (!endDate || transactionDate <= end)) {
            row.classList.remove('hidden'); // Show row if it matches the filter
        } else {
            row.classList.add('hidden'); // Hide row if it doesn't match
        }
    });
}