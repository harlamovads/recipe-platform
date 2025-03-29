document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    
    // Initialize popovers
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));
    
    // Flash messages auto-dismiss
    const flashMessages = document.querySelectorAll('.alert.alert-dismissible');
    flashMessages.forEach(message => {
        setTimeout(() => {
            const closeButton = message.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // Favorite button toggling
    const setupFavoriteButtons = () => {
        document.querySelectorAll('.favorite-btn, .favorite-toggle').forEach(btn => {
            if (!btn.hasAttribute('data-listener')) {
                btn.setAttribute('data-listener', 'true');
                btn.addEventListener('click', handleFavoriteToggle);
            }
        });
    };
    
    const handleFavoriteToggle = (event) => {
        const btn = event.currentTarget;
        const recipeId = btn.getAttribute('data-recipe-id');
        const isActive = btn.classList.contains('active') || btn.querySelector('.fas');
        
        if (isActive) {
            // Remove from favorites
            removeFavorite(recipeId, btn);
        } else {
            // Add to favorites
            addFavorite(recipeId, btn);
        }
    };
    
    const addFavorite = (recipeId, btn) => {
        fetch(`/users/recipes/${recipeId}/favorite`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update button appearance
                if (btn.classList.contains('favorite-btn')) {
                    btn.classList.add('active');
                    btn.innerHTML = '<i class="fas fa-heart"></i> Saved';
                } else {
                    const icon = btn.querySelector('i');
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                    btn.classList.remove('btn-light');
                    btn.classList.add('btn-danger');
                }
                
                // Show notification
                showNotification('Recipe added to favorites!', 'success');
            }
        })
        .catch(error => {
            console.error('Error adding favorite:', error);
            showNotification('Error adding to favorites. Please try again.', 'danger');
        });
    };
    
    const removeFavorite = (recipeId, btn) => {
        fetch(`/users/recipes/${recipeId}/favorite`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.status === 'success') {
                // Update button appearance
                if (btn.classList.contains('favorite-btn')) {
                    btn.classList.remove('active');
                    btn.innerHTML = '<i class="far fa-heart"></i> Save Recipe';
                } else {
                    const icon = btn.querySelector('i');
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-light');
                }
                
                // Show notification
                showNotification('Recipe removed from favorites', 'info');
            }
        })
        .catch(error => {
            console.error('Error removing favorite:', error);
            showNotification('Error removing from favorites. Please try again.', 'danger');
        });
    };
    
    // Check which recipes are already favorites
    const checkFavorites = () => {
        const favoriteButtons = document.querySelectorAll('.favorite-btn, .favorite-toggle');
        if (favoriteButtons.length === 0) return;
        
        fetch('/users/favorites', {
            headers: {
                'Accept': 'application/json'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(favorites => {
            const favoriteIds = favorites.map(recipe => recipe._id);
            
            favoriteButtons.forEach(btn => {
                const recipeId = btn.getAttribute('data-recipe-id');
                
                if (favoriteIds.includes(recipeId)) {
                    if (btn.classList.contains('favorite-btn')) {
                        btn.classList.add('active');
                        btn.innerHTML = '<i class="fas fa-heart"></i> Saved';
                    } else {
                        const icon = btn.querySelector('i');
                        icon.classList.remove('far');
                        icon.classList.add('fas');
                        btn.classList.remove('btn-light');
                        btn.classList.add('btn-danger');
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error fetching favorites:', error);
        });
    };
    
    // Notification system
    const showNotification = (message, type = 'info') => {
        const notificationContainer = document.getElementById('notification-container');
        
        // Create container if it doesn't exist
        if (!notificationContainer) {
            const container = document.createElement('div');
            container.id = 'notification-container';
            container.style.position = 'fixed';
            container.style.top = '20px';
            container.style.right = '20px';
            container.style.zIndex = '1050';
            container.style.maxWidth = '300px';
            document.body.appendChild(container);
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to container
        document.getElementById('notification-container').appendChild(notification);
        
        // Auto-dismiss after 3 seconds
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                notification.remove();
            }, 150);
        }, 3000);
    };
    
    // Run initialization
    setupFavoriteButtons();
    checkFavorites();
    
    // Expose global utility functions
    window.recipeApp = {
        showNotification,
        addFavorite,
        removeFavorite
    };
});