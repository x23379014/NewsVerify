document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('predictionForm');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultContainer = document.getElementById('resultContainer');
    const errorContainer = document.getElementById('errorContainer');
    const resultContent = document.getElementById('resultContent');
    const errorMessage = document.getElementById('errorMessage');

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Hide previous results
        resultContainer.style.display = 'none';
        errorContainer.style.display = 'none';
        
        // Get form data
        const headline = document.getElementById('headline').value.trim();
        const body = document.getElementById('body').value.trim();
        const url = document.getElementById('url').value.trim();
        
        if (!headline && !body) {
            showError('Please provide at least a headline or body text.');
            return;
        }
        
        // Show loading state
        submitBtn.disabled = true;
        submitText.style.display = 'none';
        loadingSpinner.style.display = 'inline-block';
        
        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    headline: headline,
                    body: body,
                    url: url
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Prediction failed');
            }
            
            // Show result
            displayResult(data);
            
        } catch (error) {
            showError(error.message || 'An error occurred. Please try again.');
        } finally {
            // Reset button state
            submitBtn.disabled = false;
            submitText.style.display = 'inline';
            loadingSpinner.style.display = 'none';
        }
    });
    
    function displayResult(data) {
        // Handle numeric labels (0/1) or text labels (fake/real)
        const predictionValue = data.prediction.toString().toLowerCase();
        const isFake = predictionValue === 'fake' || predictionValue === '0';
        const isReal = predictionValue === 'real' || predictionValue === '1';
        const confidence = (data.confidence * 100).toFixed(1);
        
        // Determine label text
        let labelText = 'UNKNOWN';
        if (isFake) {
            labelText = 'FAKE NEWS';
        } else if (isReal) {
            labelText = 'REAL NEWS';
        } else {
            labelText = `PREDICTION: ${data.prediction}`;
        }
        
        resultContent.innerHTML = `
            <div class="result-box ${isFake ? 'fake' : 'real'}">
                <div class="result-label">
                    ${labelText}
                </div>
                <div class="result-confidence">
                    Confidence: ${confidence}%
                </div>
                <div class="result-probabilities">
                    <div class="prob-item">
                        <label>Fake</label>
                        <div class="value" style="color: #c33;">
                            ${(data.probabilities.fake * 100).toFixed(1)}%
                        </div>
                    </div>
                    <div class="prob-item">
                        <label>Real</label>
                        <div class="value" style="color: #3c3;">
                            ${(data.probabilities.real * 100).toFixed(1)}%
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        resultContainer.style.display = 'block';
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    function showError(message) {
        errorMessage.textContent = message;
        errorContainer.style.display = 'block';
        errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
});

