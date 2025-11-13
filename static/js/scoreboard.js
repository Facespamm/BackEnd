/**
 * JavaScript для табло и публичного отображения
 */

class Scoreboard {
    constructor() {
        this.autoRefreshInterval = null;
        this.currentTournamentId = null;
        this.currentTatami = null;
        this.isFullscreen = false;
        this.fightTimers = new Map();

        this.initialize();
    }

    initialize() {
        this.bindEvents();
        this.startAutoRefresh();
        this.initializeLiveUpdates();
    }

    bindEvents() {
        // Переключение полноэкранного режима
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-fullscreen-toggle]')) {
                this.toggleFullscreen();
            }

            if (e.target.matches('[data-refresh-now]')) {
                this.refreshNow();
            }
        });

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            this.handleHotkeys(e);
        });

        // Изменение размера текста
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-font-size]')) {
                this.changeFontSize(e.target.getAttribute('data-font-size'));
            }
        });
    }

    // Авто-обновление данных
    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            this.refreshAllData();
        }, 5000); // Обновление каждые 5 секунд
    }

    // Обновление всех данных
    async refreshAllData() {
        await this.refreshLiveFights();
        await this.refreshTournamentStats();
        await this.refreshRecentResults();
    }

    // Обновление активных схваток
    async refreshLiveFights() {
        try {
            let url = '/scoreboard/api/live_fights';
            const params = new URLSearchParams();

            if (this.currentTournamentId) {
                params.append('tournament_id', this.currentTournamentId);
            }

            if (this.currentTatami) {
                params.append('tatami', this.currentTatami);
            }

            if (params.toString()) {
                url += '?' + params.toString();
            }

            const response = await fetch(url);
            const data = await response.json();

            this.updateLiveFightsDisplay(data.live_fights || []);

        } catch (error) {
            console.error('Error refreshing live fights:', error);
        }
    }

    // Обновление статистики турнира
    async refreshTournamentStats() {
        if (!this.currentTournamentId) return;

        try {
            const response = await fetch(`/scoreboard/api/tournament_stats/${this.currentTournamentId}`);
            const stats = await response.json();

            this.updateTournamentStats(stats);

        } catch (error) {
            console.error('Error refreshing tournament stats:', error);
        }
    }

    // Обновление последних результатов
    async refreshRecentResults() {
        try {
            const response = await fetch('/scoreboard/api/recent_results');
            const results = await response.json();

            this.updateRecentResults(results);

        } catch (error) {
            console.error('Error refreshing recent results:', error);
        }
    }

    // Обновление отображения активных схваток
    updateLiveFightsDisplay(fights) {
        const container = document.getElementById('live-fights-container');
        if (!container) return;

        if (fights.length === 0) {
            container.innerHTML = `
                <div class="text-center py-5">
                    <h3>Нет активных схваток</h3>
                    <p class="text-muted">Схватки появятся здесь, когда начнутся</p>
                </div>
            `;
            return;
        }

        let html = '';

        fights.forEach(fight => {
            html += this.renderFightCard(fight);
        });

        container.innerHTML = html;

        // Запускаем таймеры для каждой схватки
        fights.forEach(fight => {
            this.startFightTimer(fight.id, fight.timer_seconds, fight.is_golden_score);
        });
    }

    // Рендер карточки схватки
    renderFightCard(fight) {
        return `
            <div class="live-fight-card" id="fight-${fight.id}">
                <div class="row align-items-center">
                    <div class="col-md-2">
                        <div class="text-center">
                            <h4 class="mb-0">Тами ${fight.tatami}</h4>
                            <small>Схватка ${fight.fight_number}</small>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="athlete-scoreboard athlete-white">
                            <div class="athlete-name">${fight.white_athlete.name}</div>
                            <div class="athlete-club">${fight.white_athlete.club}</div>
                            <div class="athlete-points" id="white-score-${fight.id}">
                                ${fight.scores.white}
                            </div>
                            <div class="penalty-indicators" id="white-penalties-${fight.id}">
                                ${this.renderPenalties(fight.penalties.white)}
                            </div>
                        </div>
                    </div>

                    <div class="col-md-2">
                        <div class="fight-timer ${fight.is_golden_score ? 'golden' : ''}" id="timer-${fight.id}">
                            ${JudoSystem.formatDuration(fight.timer_seconds)}
                        </div>
                        <div class="text-center">
                            <small>${fight.category}</small><br>
                            <small>${fight.tournament}</small>
                        </div>
                    </div>

                    <div class="col-md-3">
                        <div class="athlete-scoreboard athlete-blue">
                            <div class="athlete-name">${fight.blue_athlete.name}</div>
                            <div class="athlete-club">${fight.blue_athlete.club}</div>
                            <div class="athlete-points" id="blue-score-${fight.id}">
                                ${fight.scores.blue}
                            </div>
                            <div class="penalty-indicators" id="blue-penalties-${fight.id}">
                                ${this.renderPenalties(fight.penalties.blue)}
                            </div>
                        </div>
                    </div>

                    <div class="col-md-2">
                        <div class="text-center">
                            <span class="live-indicator"></span>
                            <strong>LIVE</strong>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Рендер штрафов
    renderPenalties(count) {
        let html = '';
        for (let i = 0; i < 3; i++) {
            html += `<div class="penalty-shido ${i < count ? 'active' : ''}"></div>`;
        }
        return html;
    }

    // Запуск таймера для схватки
    startFightTimer(fightId, initialSeconds, isGoldenScore) {
        // Останавливаем предыдущий таймер если есть
        if (this.fightTimers.has(fightId)) {
            clearInterval(this.fightTimers.get(fightId));
        }

        let seconds = initialSeconds;
        const timerElement = document.getElementById(`timer-${fightId}`);

        if (!timerElement) return;

        const timerInterval = setInterval(() => {
            if (seconds > 0) {
                seconds--;
                timerElement.textContent = JudoSystem.formatDuration(seconds);

                // Обновление цвета при приближении к 0
                if (seconds <= 10 && !isGoldenScore) {
                    timerElement.classList.add('timer-warning');
                }

                if (seconds <= 5) {
                    timerElement.classList.add('timer-critical');
                }
            } else {
                clearInterval(timerInterval);
                this.fightTimers.delete(fightId);

                if (!isGoldenScore) {
                    // Переход в золотой скор
                    timerElement.classList.add('golden');
                    timerElement.textContent = 'GOLDEN SCORE';
                    timerElement.classList.remove('timer-warning', 'timer-critical');
                } else {
                    timerElement.textContent = 'TIME UP';
                }
            }
        }, 1000);

        this.fightTimers.set(fightId, timerInterval);
    }

    // Обновление статистики турнира
    updateTournamentStats(stats) {
        const container = document.getElementById('tournament-stats');
        if (!container) return;

        container.innerHTML = `
            <div class="row text-center">
                <div class="col-md-3">
                    <div class="stat-item">
                        <h3>${stats.total_fights || 0}</h3>
                        <p>Всего схваток</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h3>${stats.completed_fights || 0}</h3>
                        <p>Завершено</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h3>${stats.ippon_count || 0}</h3>
                        <p>Иппонов</p>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="stat-item">
                        <h3>${Math.round(stats.average_fight_duration / 60) || 0}</h3>
                        <p>Среднее время (мин)</p>
                    </div>
                </div>
            </div>
        `;
    }

    // Обновление последних результатов
    updateRecentResults(results) {
        const container = document.getElementById('recent-results');
        if (!container) return;

        if (results.length === 0) {
            container.innerHTML = '<p class="text-muted">Нет завершенных схваток</p>';
            return;
        }

        let html = '<div class="list-group">';

        results.forEach(result => {
            html += `
                <div class="list-group-item">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">${result.category} - ${result.tournament}</h6>
                        <small>${result.end_time}</small>
                    </div>
                    <p class="mb-1">
                        <strong>${result.winner}</strong> 
                        ${result.winner_club ? `(${result.winner_club})` : ''}
                    </p>
                    <small class="text-muted">${result.victory_type} • ${JudoSystem.formatDuration(result.fight_duration)}</small>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;
    }

    // Инициализация live updates через WebSocket (если доступно)
    initializeLiveUpdates() {
        // В будущем можно добавить WebSocket для реального времени
        console.log('Live updates initialized');
    }

    // Обработка горячих клавиш
    handleHotkeys(event) {
        if (event.ctrlKey || event.altKey) return;

        switch (event.key) {
            case 'F5':
                event.preventDefault();
                this.refreshNow();
                break;

            case 'F11':
                event.preventDefault();
                this.toggleFullscreen();
                break;

            case '+':
                event.preventDefault();
                this.changeFontSize('increase');
                break;

            case '-':
                event.preventDefault();
                this.changeFontSize('decrease');
                break;

            case '0':
                event.preventDefault();
                this.changeFontSize('reset');
                break;
        }
    }

    // Переключение полноэкранного режима
    toggleFullscreen() {
        if (!this.isFullscreen) {
            this.enterFullscreen();
        } else {
            this.exitFullscreen();
        }
    }

    enterFullscreen() {
        const elem = document.documentElement;

        if (elem.requestFullscreen) {
            elem.requestFullscreen();
        } else if (elem.webkitRequestFullscreen) {
            elem.webkitRequestFullscreen();
        } else if (elem.msRequestFullscreen) {
            elem.msRequestFullscreen();
        }

        this.isFullscreen = true;
        document.body.classList.add('fullscreen');

        JudoSystem.showNotification('Полноэкранный режим включен', 'info');
    }

    exitFullscreen() {
        if (document.exitFullscreen) {
            document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
            document.webkitExitFullscreen();
        } else if (document.msExitFullscreen) {
            document.msExitFullscreen();
        }

        this.isFullscreen = false;
        document.body.classList.remove('fullscreen');

        JudoSystem.showNotification('Полноэкранный режим выключен', 'info');
    }

    // Изменение размера шрифта
    changeFontSize(action) {
        const mainElement = document.querySelector('main');
        const currentSize = parseFloat(getComputedStyle(mainElement).fontSize);

        let newSize;
        switch (action) {
            case 'increase':
                newSize = currentSize * 1.2;
                break;
            case 'decrease':
                newSize = currentSize * 0.8;
                break;
            case 'reset':
            default:
                newSize = 16; // базовый размер
                break;
        }

        // Ограничиваем размер
        newSize = Math.max(12, Math.min(48, newSize));
        mainElement.style.fontSize = newSize + 'px';

        // Сохраняем в localStorage
        localStorage.setItem('scoreboardFontSize', newSize);
    }

    // Принудительное обновление
    refreshNow() {
        this.refreshAllData();
        JudoSystem.showNotification('Данные обновлены', 'success');
    }

    // Установка текущего турнира
    setCurrentTournament(tournamentId) {
        this.currentTournamentId = tournamentId;
        this.refreshAllData();
    }

    // Установка текущего татами
    setCurrentTatami(tatami) {
        this.currentTatami = tatami;
        this.refreshAllData();
    }

    // Очистка при уничтожении
    destroy() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }

        // Останавливаем все таймеры схваток
        this.fightTimers.forEach((timer, fightId) => {
            clearInterval(timer);
        });
        this.fightTimers.clear();
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.scoreboard = new Scoreboard();

    // Восстанавливаем размер шрифта из localStorage
    const savedFontSize = localStorage.getItem('scoreboardFontSize');
    if (savedFontSize) {
        document.querySelector('main').style.fontSize = savedFontSize + 'px';
    }
});

// Глобальные функции для использования в HTML
function setCurrentTournament(tournamentId) {
    if (window.scoreboard) {
        window.scoreboard.setCurrentTournament(tournamentId);
    }
}

function setCurrentTatami(tatami) {
    if (window.scoreboard) {
        window.scoreboard.setCurrentTatami(tatami);
    }
}

function toggleFullscreen() {
    if (window.scoreboard) {
        window.scoreboard.toggleFullscreen();
    }
}

function refreshScoreboard() {
    if (window.scoreboard) {
        window.scoreboard.refreshNow();
    }
}

// Функции для работы с турнирными сетками
function initializeBracketView(bracketData) {
    // Инициализация визуализации турнирной сетки
    console.log('Initializing bracket view with data:', bracketData);

    // Здесь можно добавить логику для отрисовки сетки
    // Например, с использованием библиотеки для bracket visualization
}

// Функции для работы с результатами
function displayCategoryResults(results) {
    const container = document.getElementById('category-results');
    if (!container) return;

    let html = '';

    results.forEach((category, index) => {
        html += `
            <div class="category-result mb-4">
                <h4 class="category-title">${category.category}</h4>
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Место</th>
                                <th>Участник</th>
                                <th>Клуб</th>
                                <th>Победы</th>
                                <th>Схватки</th>
                                <th>Очки</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${category.athletes.map((athlete, pos) => `
                                <tr>
                                    <td>${pos + 1}</td>
                                    <td>${athlete.athlete.full_name}</td>
                                    <td>${athlete.athlete.club?.name || ''}</td>
                                    <td>${athlete.victories}</td>
                                    <td>${athlete.fights}</td>
                                    <td>${athlete.total_points}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

// Экспорт данных
function exportTournamentResults(tournamentId, format = 'pdf') {
    const url = `/public/results/export/${tournamentId}?format=${format}`;
    window.open(url, '_blank');
}