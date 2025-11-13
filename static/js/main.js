/**
 * Основные JavaScript функции для Judo Tournament System
 */

// Глобальные переменные
let autoRefreshIntervals = {};

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeTooltips();
    initializeAutoRefresh();
    initializeFormValidations();
    initializeSearchFunctions();
});

// Инициализация tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Авто-обновление для страниц с live данными
function initializeAutoRefresh() {
    const autoRefreshElements = document.querySelectorAll('[data-auto-refresh]');

    autoRefreshElements.forEach(element => {
        const interval = parseInt(element.getAttribute('data-auto-refresh')) || 5000;
        const url = element.getAttribute('data-refresh-url');

        if (url) {
            startAutoRefresh(element, url, interval);
        }
    });
}

// Запуск авто-обновления
function startAutoRefresh(element, url, interval) {
    const key = url + '-' + interval;

    if (autoRefreshIntervals[key]) {
        clearInterval(autoRefreshIntervals[key]);
    }

    autoRefreshIntervals[key] = setInterval(() => {
        fetchData(url, element);
    }, interval);
}

// Остановка авто-обновления
function stopAutoRefresh(url, interval) {
    const key = url + '-' + interval;
    if (autoRefreshIntervals[key]) {
        clearInterval(autoRefreshIntervals[key]);
        delete autoRefreshIntervals[key];
    }
}

// Загрузка данных через AJAX
async function fetchData(url, targetElement = null) {
    try {
        const response = await fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (targetElement) {
            updateElementContent(targetElement, data);
        }

        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        showNotification('Ошибка загрузки данных', 'danger');
    }
}

// Обновление содержимого элемента
function updateElementContent(element, data) {
    if (typeof data === 'string') {
        element.innerHTML = data;
    } else if (data.html) {
        element.innerHTML = data.html;
    } else if (data.content) {
        element.innerHTML = data.content;
    }

    // Реинициализация tooltips после обновления контента
    initializeTooltips();
}

// Показать уведомление
function showNotification(message, type = 'info', duration = 5000) {
    const alertClass = `alert-${type}`;
    const alertId = 'notification-' + Date.now();

    const alertHtml = `
        <div id="${alertId}" class="alert ${alertClass} alert-dismissible fade show">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    // Добавляем в контейнер для уведомлений или создаем его
    let notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.className = 'position-fixed top-0 end-0 p-3';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }

    notificationContainer.insertAdjacentHTML('beforeend', alertHtml);

    // Автоматическое скрытие
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

// Валидация форм
function initializeFormValidations() {
    const forms = document.querySelectorAll('form[needs-validation]');

    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }

            form.classList.add('was-validated');
        });
    });
}

// Функции поиска
function initializeSearchFunctions() {
    // Поиск с автодополнением
    const searchInputs = document.querySelectorAll('[data-autocomplete-url]');

    searchInputs.forEach(input => {
        let timeoutId;

        input.addEventListener('input', function() {
            clearTimeout(timeoutId);
            timeoutId = setTimeout(() => {
                performSearch(this);
            }, 300);
        });
    });
}

// Выполнение поиска
async function performSearch(input) {
    const url = input.getAttribute('data-autocomplete-url');
    const query = input.value.trim();
    const resultsContainer = document.getElementById(input.getAttribute('data-results-container'));

    if (query.length < 2) {
        if (resultsContainer) resultsContainer.innerHTML = '';
        return;
    }

    try {
        const searchUrl = `${url}?q=${encodeURIComponent(query)}`;
        const data = await fetchData(searchUrl);

        if (resultsContainer && data) {
            displaySearchResults(resultsContainer, data);
        }
    } catch (error) {
        console.error('Search error:', error);
    }
}

// Отображение результатов поиска
function displaySearchResults(container, results) {
    if (!results || results.length === 0) {
        container.innerHTML = '<div class="dropdown-item text-muted">Ничего не найдено</div>';
        return;
    }

    let html = '';
    results.forEach(item => {
        html += `
            <a href="${item.url}" class="dropdown-item">
                <strong>${item.name}</strong>
                ${item.club ? `<br><small class="text-muted">${item.club}</small>` : ''}
                ${item.city ? `<br><small class="text-muted">${item.city}</small>` : ''}
            </a>
        `;
    });

    container.innerHTML = html;
}

// Подтверждение действий
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Удаление элемента с подтверждением
function confirmDelete(element, message = 'Вы уверены, что хотите удалить этот элемент?') {
    confirmAction(message, () => {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = element.getAttribute('data-delete-url') || element.href;

        const csrfToken = document.querySelector('meta[name="csrf-token"]');
        if (csrfToken) {
            const input = document.createElement('input');
            input.type = 'hidden';
            input.name = 'csrf_token';
            input.value = csrfToken.getAttribute('content');
            form.appendChild(input);
        }

        document.body.appendChild(form);
        form.submit();
    });

    return false;
}

// Форматирование времени
function formatDuration(seconds) {
    if (!seconds && seconds !== 0) return '--:--';

    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Форматирование даты
function formatDate(dateString, options = {}) {
    const date = new Date(dateString);
    const defaultOptions = {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    };

    return date.toLocaleDateString('ru-RU', { ...defaultOptions, ...options });
}

// Копирование в буфер обмена
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Скопировано в буфер обмена', 'success', 2000);
    }).catch(err => {
        console.error('Copy failed:', err);
        showNotification('Ошибка копирования', 'danger');
    });
}

// Экспорт данных
function exportData(url, format = 'csv') {
    const exportUrl = `${url}?format=${format}`;
    window.open(exportUrl, '_blank');
}

// Загрузка файла
function uploadFile(input, progressCallback = null) {
    return new Promise((resolve, reject) => {
        const file = input.files[0];
        if (!file) {
            reject(new Error('Файл не выбран'));
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        const xhr = new XMLHttpRequest();

        if (progressCallback) {
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    progressCallback(percentComplete);
                }
            });
        }

        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(new Error(`Upload failed: ${xhr.status}`));
            }
        });

        xhr.addEventListener('error', () => {
            reject(new Error('Upload failed'));
        });

        xhr.open('POST', input.getAttribute('data-upload-url'));
        xhr.send(formData);
    });
}

// Управление модальными окнами
function showModal(modalId) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    modal.show();
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// Утилиты для работы с API
const API = {
    async get(url) {
        const response = await fetch(url);
        return response.json();
    },

    async post(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async put(url, data) {
        const response = await fetch(url, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    async delete(url) {
        const response = await fetch(url, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// Глобальный экспорт функций
window.JudoSystem = {
    showNotification,
    confirmAction,
    confirmDelete,
    formatDuration,
    formatDate,
    copyToClipboard,
    exportData,
    uploadFile,
    showModal,
    hideModal,
    API
};