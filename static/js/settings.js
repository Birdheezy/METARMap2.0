console.log('settings.js loaded');
// Save scroll position on form submission
function saveScrollPosition() {
    sessionStorage.setItem('scrollPosition', window.scrollY);
}

    // Restore scroll position on page reload
    document.addEventListener('DOMContentLoaded', function () {
        const scrollPosition = sessionStorage.getItem('scrollPosition');
        if (scrollPosition) {
            window.scrollTo(0, parseInt(scrollPosition));
            sessionStorage.removeItem('scrollPosition');
        }
    });

    // Scan for networks when the "Scan" button is clicked
    document.getElementById('scan-button').addEventListener('click', function () {
        let scanButton = document.getElementById('scan-button');
        let ssidSelect = document.getElementById('ssid-select');
        let connectionStatus = document.getElementById('connection-status');

        // Disable the button and show a loading message
        scanButton.disabled = true;
        connectionStatus.textContent = 'Scanning for networks...';

        fetch('/scan-networks')
            .then(response => response.json())
            .then(data => {
                ssidSelect.innerHTML = '<option value="">Select a network</option>';

                if (data.networks && data.networks.length > 0) {
                    data.networks.forEach(network => {
                        let option = document.createElement('option');
                        option.value = network.ssid;
                        option.textContent = `${network.ssid} (Signal: ${network.signal}%)`;
                        ssidSelect.appendChild(option);
                    });
                    connectionStatus.textContent = 'Scan complete. Select a network.';
                } else {
                    connectionStatus.textContent = 'No networks found. Try scanning again.';
                }
            })
            .catch(error => {
                console.error('Error scanning networks:', error);
                connectionStatus.textContent = 'An error occurred while scanning.';
            })
            .finally(() => {
                // Re-enable the button after the scan completes
                scanButton.disabled = false;
            });
    });

    // Connect to the selected network when "Connect" is clicked
    document.getElementById('connect-button').addEventListener('click', function () {
        let ssid = document.getElementById('ssid-select').value;
        let password = document.getElementById('wifi-password').value;
        let connectionStatus = document.getElementById('connection-status');

        if (!ssid) {
            connectionStatus.textContent = 'Please select a network.';
            return;
        }

        fetch('/connect-to-network', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ ssid: ssid, password: password })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    connectionStatus.textContent = 'Connected successfully!';
                } else {
                    connectionStatus.textContent = `Error: ${data.error}`;
                }
            })
            .catch(error => {
                console.error('Error connecting to network:', error);
                connectionStatus.textContent = 'An error occurred while connecting.';
            });
    });

    document.addEventListener('DOMContentLoaded', function() {
        const textarea = document.getElementById('airportsText');
        const lineNumbers = document.getElementById('line-numbers');

        function updateLineNumbers() {
            const lines = textarea.value.split('\n').length;
            let lineNumbersHtml = '';
            for (let i = 1; i <= lines; i++) {
                lineNumbersHtml += `${i}<br>`;
            }
            lineNumbers.innerHTML = lineNumbersHtml;
        }

        // Sync scrolling between the textarea and the line numbers
        textarea.addEventListener('scroll', function () {
            lineNumbers.style.transform = `translateY(-${textarea.scrollTop}px)`;
        });

        // Update line numbers on input
        textarea.addEventListener('input', updateLineNumbers);

        // Initial update on page load
        updateLineNumbers();
    });

function saveScrollPosition() {
    sessionStorage.setItem('scrollPosition', window.scrollY);
}

function saveAndRestart() {
  // Trigger the form submission first
  document.forms[0].submit();

  // After a slight delay, make a request to restart the metar service
  setTimeout(() => {
    fetch('/restart_metar')
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Failed to restart METAR service');
      })
      .then(data => {
        if (data.success) {
          alert('Settings saved and METAR service restarted successfully!');
        } else {
          console.error('Settings saved but failed to restart METAR service.');
        }
      })
      .catch(error => {
        console.error('Error restarting METAR service:', error);
      });
  }, 500); // Delay to allow settings to save
}


// Restore the scroll position after the page reloads
document.addEventListener('DOMContentLoaded', function() {
    const scrollPosition = sessionStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        sessionStorage.removeItem('scrollPosition');
    }
});

// JavaScript for toast notifications
function showToast(message, category) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerText = message;
    toast.classList.add(category);
    document.body.appendChild(toast);
    setTimeout(function() {
        toast.classList.add('show');
    }, 100);
    setTimeout(function() {
        toast.classList.remove('show');
        document.body.removeChild(toast);
    }, 8000);
}

document.addEventListener('DOMContentLoaded', function() {
    if (typeof messages !== 'undefined' && messages.length > 0) {
        messages.forEach(function(msg) {
            showToast(msg.message, msg.category);
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
        // Add click and keypress event listener to tooltip icons
        const tooltipIcons = document.querySelectorAll('.tooltip-icon');

        tooltipIcons.forEach(icon => {
            icon.addEventListener('click', function() {
                toggleTooltip(this);
            });

            icon.addEventListener('keypress', function(event) {
                if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault();
                    toggleTooltip(this);
                }
            });
        });

        function toggleTooltip(icon) {
            const tooltipContent = icon.parentElement.nextElementSibling;
            const isExpanded = icon.getAttribute('aria-expanded') === 'true';

            if (isExpanded) {
                tooltipContent.style.display = 'none';
                icon.setAttribute('aria-expanded', 'false');
            } else {
                tooltipContent.style.display = 'block';
                icon.setAttribute('aria-expanded', 'true');
            }
        }
    });
