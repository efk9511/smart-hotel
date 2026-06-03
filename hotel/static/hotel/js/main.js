(function() {
    var theme = getCookie('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.body.classList.add(theme + '-theme');
})();

function getCookie(name) {
    var value = '; ' + document.cookie;
    var parts = value.split('; ' + name + '=');
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        document.querySelectorAll('.alert-dismissible').forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-delete-url]').forEach(function(el) {
        el.addEventListener('click', function(e) {
            e.preventDefault();
            var url = this.dataset.deleteUrl;
            var name = this.dataset.itemName || 'this item';
            var msg = document.getElementById('deleteModalMessage');
            if (msg) msg.textContent = 'Are you sure you want to delete "' + name + '"?';
            var confirmBtn = document.getElementById('deleteModalConfirm');
            if (confirmBtn) confirmBtn.href = url;
            var modal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
            modal.show();
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.ajax-status-form').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            var formData = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                },
                body: formData
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.success) {
                    location.reload();
                }
            })
            .catch(function() {
                location.reload();
            });
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) {
        return new bootstrap.Tooltip(el);
    });
});

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.alert-success').forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 4000);
    });
});
