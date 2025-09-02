// JavaScript principal para MM Conecta Leads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize notifications
    loadNotifications();
    
    // Set up periodic notification updates
    setInterval(loadNotifications, 30000); // Update every 30 seconds

    // Auto-hide flash messages after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Form validation enhancement
    enhanceFormValidation();

    // Real-time updates for dashboard
    if (window.location.pathname.includes('dashboard')) {
        setInterval(updateDashboardMetrics, 60000); // Update every minute
    }
});

// Notification system
function loadNotifications() {
    // Only load notifications if user is logged in
    if (!document.querySelector('.navbar-nav')) return;

    fetch('/api/notifications')
        .then(response => response.json())
        .then(notifications => {
            updateNotificationUI(notifications);
        })
        .catch(error => {
            console.error('Error loading notifications:', error);
        });
}

function updateNotificationUI(notifications) {
    const badge = document.getElementById('notification-badge');
    const dropdown = document.getElementById('notification-dropdown');
    
    if (!badge || !dropdown) return;

    // Update badge count
    const totalCount = notifications.reduce((sum, notif) => sum + (notif.count || 1), 0);
    
    if (totalCount > 0) {
        badge.textContent = totalCount;
        badge.style.display = 'inline';
    } else {
        badge.style.display = 'none';
    }

    // Update dropdown content
    if (notifications.length > 0) {
        dropdown.innerHTML = '';
        
        notifications.forEach(notification => {
            const item = document.createElement('li');
            const link = document.createElement('a');
            link.className = 'dropdown-item';
            link.innerHTML = `
                <i class="fas fa-${getNotificationIcon(notification.type)} me-2"></i>
                ${notification.message}
            `;
            
            // Add click handler for different notification types
            if (notification.type === 'new_leads') {
                link.href = '/broker/leads?status=novo';
            } else if (notification.type === 'follow_ups') {
                link.href = '/broker/leads';
            }
            
            item.appendChild(link);
            dropdown.appendChild(item);
        });

        // Add "Mark all as read" option
        const divider = document.createElement('li');
        divider.innerHTML = '<hr class="dropdown-divider">';
        dropdown.appendChild(divider);

        const markAllItem = document.createElement('li');
        const markAllLink = document.createElement('a');
        markAllLink.className = 'dropdown-item text-center text-muted';
        markAllLink.innerHTML = '<small>Notificações são atualizadas automaticamente</small>';
        markAllItem.appendChild(markAllLink);
        dropdown.appendChild(markAllItem);
    } else {
        dropdown.innerHTML = '<li><span class="dropdown-item-text text-muted">Nenhuma nova notificação</span></li>';
    }
}

function getNotificationIcon(type) {
    const icons = {
        'new_leads': 'exclamation-circle',
        'follow_ups': 'calendar-alt',
        'lead_update': 'edit',
        'system': 'info-circle'
    };
    return icons[type] || 'bell';
}

// Form validation enhancement
function enhanceFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Add loading state to submit button
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
                submitBtn.disabled = true;
                
                // Re-enable button after 5 seconds as fallback
                setTimeout(() => {
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }, 5000);
            }
        });

        // Real-time validation for email fields
        const emailInputs = form.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateEmail(this);
            });
        });

        // Real-time validation for phone fields
        const phoneInputs = form.querySelectorAll('input[name="phone"], input[type="tel"]');
        phoneInputs.forEach(input => {
            input.addEventListener('input', function() {
                formatPhoneNumber(this);
            });
        });
    });
}

function validateEmail(input) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const isValid = emailRegex.test(input.value);
    
    input.classList.remove('is-valid', 'is-invalid');
    
    if (input.value) {
        if (isValid) {
            input.classList.add('is-valid');
        } else {
            input.classList.add('is-invalid');
        }
    }
}

function formatPhoneNumber(input) {
    // Simple phone formatting (can be enhanced based on requirements)
    let value = input.value.replace(/\D/g, '');
    
    if (value.length >= 10) {
        value = value.replace(/(\d{3})(\d{3})(\d{4})/, '($1) $2-$3');
    } else if (value.length >= 6) {
        value = value.replace(/(\d{3})(\d{3})/, '($1) $2');
    } else if (value.length >= 3) {
        value = value.replace(/(\d{3})/, '($1)');
    }
    
    input.value = value;
}

// Dashboard metrics update
function updateDashboardMetrics() {
    // This could be enhanced to fetch real-time metrics
    // For now, we'll just add visual feedback
    const metricCards = document.querySelectorAll('.card.bg-primary, .card.bg-success, .card.bg-info, .card.bg-warning');
    
    metricCards.forEach(card => {
        card.style.transform = 'scale(1.02)';
        setTimeout(() => {
            card.style.transform = 'scale(1)';
        }, 200);
    });
}

// Utility functions
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            const bsAlert = new bootstrap.Alert(toast);
            bsAlert.close();
        }
    }, 4000);
}

// Lead management specific functions
function updateLeadStatus(leadId, status) {
    const formData = new FormData();
    formData.append('status', status);
    
    fetch(`/broker/leads/${leadId}/update`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            showToast('Status do lead atualizado com sucesso', 'success');
            // Reload page to show updated status
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showToast('Falha ao atualizar status do lead', 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating lead:', error);
        showToast('Erro ao atualizar status do lead', 'danger');
    });
}

// Export functions for global access
window.showToast = showToast;
window.updateLeadStatus = updateLeadStatus;

// Enhanced table interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to table rows
    const tableRows = document.querySelectorAll('table tbody tr');
    tableRows.forEach(row => {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
        });
        
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });

    // Add confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('button[onclick*="delete"], form[action*="delete"] button[type="submit"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Enhanced search functionality (if search inputs exist)
    const searchInputs = document.querySelectorAll('input[type="search"], input[placeholder*="search"]');
    searchInputs.forEach(input => {
        let searchTimeout;
        input.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Add search functionality here if needed
                console.log('Searching for:', this.value);
            }, 300);
        });
    });
});

// Print functionality
function printPage() {
    window.print();
}

// Copy to clipboard functionality
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copiado para a área de transferência', 'success');
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
        showToast('Falha ao copiar para a área de transferência', 'danger');
    });
}

// Date formatting utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMins < 1) return 'Agora mesmo';
    if (diffMins < 60) return `${diffMins} minutos atrás`;
    if (diffHours < 24) return `${diffHours} horas atrás`;
    if (diffDays < 7) return `${diffDays} dias atrás`;
    return date.toLocaleDateString();
}

// Make utility functions globally available
window.printPage = printPage;
window.copyToClipboard = copyToClipboard;
window.formatDate = formatDate;
window.formatRelativeTime = formatRelativeTime;
