// File: static/js/app.js
// --- a/file:///c%3A/Users/user/Desktop/pythonProject/static/js/app.js
        document.addEventListener('DOMContentLoaded', function() {
            const themeOptions = document.querySelectorAll('.theme-option');
            const previewContainer = document.querySelector('.preview-container');
            const recipientInput = document.getElementById('recipient');
            const messageInput = document.getElementById('message');
            const sendBtn = document.getElementById('sendBtn');
            const previewRecipient = document.getElementById('previewRecipient');
            const previewMessage = document.getElementById('previewMessage');
            const successMessage = document.getElementById('successMessage');
            const sentToSpan = document.getElementById('sentTo');
            
            // Set default preview
            previewRecipient.textContent = '@username';
            
            // Theme selection
            themeOptions.forEach(option => {
                option.addEventListener('click', function() {
                    themeOptions.forEach(opt => opt.classList.remove('active'));
                    this.classList.add('active');
                    
                    const theme = this.getAttribute('data-theme');
                    previewContainer.className = 'preview-container theme-' + theme;
                });
            });
            
            // Update preview as user types
            recipientInput.addEventListener('input', function() {
                previewRecipient.textContent = this.value || '@username';
            });
            
            messageInput.addEventListener('input', function() {
                previewMessage.textContent = this.value || 'Your personalized message will appear here...';
            });
            
            // Send button functionality
            sendBtn.addEventListener('click', function() {
                const recipient = recipientInput.value.trim();
                const message = messageInput.value.trim();
                
                if (!recipient) {
                    alert('Please enter a recipient username');
                    return;
                }
                
                if (!message) {
                    alert('Please enter a message');
                    return;
                }
                
                // Show success message
                sentToSpan.textContent = recipient;
                successMessage.style.display = 'block';
                
                // Reset form after 3 seconds
                setTimeout(() => {
                    recipientInput.value = '';
                    messageInput.value = '';
                    previewRecipient.textContent = '@username';
                    previewMessage.textContent = 'Your personalized message will appear here...';
                    successMessage.style.display = 'none';
                }, 5000);
            });
        });