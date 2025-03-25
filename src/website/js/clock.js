document.addEventListener('DOMContentLoaded', function() {
    const clockElement = document.getElementById('clock');
    const dateElement = document.createElement('div');
    dateElement.classList.add('date-widget');
    clockElement.parentNode.insertBefore(dateElement, clockElement.nextSibling);

    function updateClock() {
        const now = new Date();
        
        // Time formatting
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        // Date formatting
        const days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
        
        const dayName = days[now.getDay()];
        const monthName = months[now.getMonth()];
        const date = now.getDate();
        const year = now.getFullYear();

        // Update clock
        clockElement.innerHTML = `${hours}:${minutes}:${seconds}`;
        
        // Update date
        dateElement.innerHTML = `${dayName}, ${monthName} ${date}, ${year}`;

        // Add pulse effect on second change
        clockElement.classList.add('pulse');
        setTimeout(() => {
            clockElement.classList.remove('pulse');
        }, 500);
    }

    // Initial call
    updateClock();

    // Update every second
    setInterval(updateClock, 1000);
});