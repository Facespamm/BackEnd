/**
 * JavaScript для судейского интерфейса
 */

class RefereeInterface {
    constructor() {
        this.currentFightId = null;
        this.timerInterval = null;
        this.autoRefreshInterval = null;
        this.isFullscreen = false;

        this.initialize();
    }

    initialize() {
        this.bindEvents();
        this.startAutoRefresh();
        this.initializeTimer();
    }

    bindEvents() {
        // Кнопки управления схваткой
        document.addEventListener('click', (e) => {
            if (e.target.matches('[data-fight-action]')) {
                this.handleFightAction(e);
            }

            if (e.target.matches('[data-score-action]')) {
                this.handleScoreAction(e);
            }

            if (e.target.matches('[data-timer-action]')) {
                this.handleTimerAction(e);
            }
        });

        // Полноэкранный режим
        document.addEventListener('keydown', (e) => {
            if (e.key === 'F11') {
                e.preventDefault();
                this.toggleFullscreen();
            }

            if (e.key === 'Escape' && this.isFullscreen) {
                this.exitFullscreen();
            }
        });

        // Горячие клавиши
        document.addEventListener('keydown', (e) => {
            this.handleHotkeys(e);
        });
    }

    // Обработка действий со схваткой
    async handleFightAction(event) {
        const button = event.target.closest('[data-fight-action]');
        const action = button.getAttribute('data-fight-action');
        const fightId = button.getAttribute('data-fight-id') || this.currentFightId;

        if (!fightId) {
            JudoSystem.showNotification('Схватка не выбрана', 'warning');
            return;
        }

        try {
            let url;
            let data = {};

            switch (action) {
                case 'start':
                    url = `/referee/fight/${fightId}/start`;
                    break;

                case 'pause':
                    url = `/referee/fight/${fightId}/pause`;
                    break;

                case 'resume':
                    url = `/referee/fight/${fightId}/resume`;
                    break;

                case 'complete':
                    const winner = prompt('ID победителя:');
                    const victoryType = prompt('Тип победы (IPPON, WAZAARI, SHIDO):');
                    if (winner && victoryType) {
                        url = `/referee/fight/${fightId}/complete`;
                        data = {
                            winner_id: winner,
                            victory_type: victoryType
                        };
                    } else {
                        return;
                    }
                    break;

                default:
                    console.warn('Unknown action:', action);
                    return;
            }

            const response = await this.sendAction(url, data);

            if (response.success) {
                JudoSystem.showNotification('Действие выполнено', 'success');
                this.refreshFightStatus();
            } else {
                JudoSystem.showNotification(response.error || 'Ошибка', 'danger');
            }

        } catch (error) {
            console.error('Action error:', error);
            JudoSystem.showNotification('Ошибка выполнения', 'danger');
        }
    }

    // Обработка добавления оценок
    async handleScoreAction(event) {
        const button = event.target.closest('[data-score-action]');
        const athleteColor = button.getAttribute('data-athlete-color');
        const scoreType = button.getAttribute('data-score-type');
        const fightId = button.getAttribute('data-fight-id') || this.currentFightId;

        if (!fightId) {
            JudoSystem.showNotification('Схватка не выбрана', 'warning');
            return;
        }

        try {
            const response = await this.sendAction(`/referee/fight/${fightId}/add_score`, {
                athlete_color: athleteColor,
                score_type: scoreType
            });

            if (response.success) {
                this.animateScore(athleteColor, scoreType);
                this.refreshFightStatus();
            } else {
                JudoSystem.showNotification(response.error || 'Ошибка', 'danger');
            }

        } catch (error) {
            console.error('Score error:', error);
            JudoSystem.showNotification('Ошибка добавления оценки', 'danger');
        }
    }

    // Обработка действий с таймером
    async handleTimerAction(event) {
        const button = event.target.closest('[data-timer-action]');
        const action = button.getAttribute('data-timer-action');
        const fightId = button.getAttribute('data-fight-id') || this.currentFightId;

        if (!fightId) return;

        switch (action) {
            case 'set':
                const seconds = prompt('Установить время (секунды):');
                if (seconds) {
                    await this.setTimer(fightId, parseInt(seconds));
                }
                break;

            case 'reset':
                await this.resetTimer(fightId);
                break;
        }
    }

    // Отправка действия на сервер
    async sendAction(url, data = {}) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams(data)
        });

        return await response.json();
    }

    // Анимация добавления оценки
    animateScore(athleteColor, scoreType) {
        const scoreElement = document.querySelector(`[data-athlete="${athleteColor}"] [data-score-display]`);
        const penaltyElement = document.querySelector(`[data-athlete="${athleteColor}"] [data-penalties]`);

        if (scoreElement) {
            scoreElement.classList.add('pulse');
            setTimeout(() => {
                scoreElement.classList.remove('pulse');
            }, 1000);
        }

        if (penaltyElement && scoreType === 'SHIDO') {
            penaltyElement.classList.add('pulse');
            setTimeout(() => {
                penaltyElement.classList.remove('pulse');
            }, 1000);
        }
    }

    // Инициализация таймера
    initializeTimer() {
        const timerElement = document.getElementById('fight-timer');
        if (!timerElement) return;

        this.updateTimerDisplay();
        this.timerInterval = setInterval(() => {
            this.updateTimerDisplay();
        }, 1000);
    }

    // Обновление отображения таймера
    updateTimerDisplay() {
        const timerElement = document.getElementById('fight-timer');
        const secondsElement = document.getElementById('timer-seconds');

        if (!timerElement || !secondsElement) return;

        let seconds = parseInt(secondsElement.textContent) || 0;

        // Если схватка активна и не на паузе, уменьшаем время
        const isPaused = timerElement.classList.contains('paused');
        const isActive = timerElement.classList.contains('active');

        if (isActive && !isPaused && seconds > 0) {
            seconds--;
            secondsElement.textContent = seconds;

            // Обновляем на сервере каждые 5 секунд
            if (seconds % 5 === 0 && this.currentFightId) {
                this.updateServerTimer(seconds);
            }

            // Переход в золотой скор
            if (seconds === 0 && !timerElement.classList.contains('golden')) {
                this.enterGoldenScore();
            }
        }

        // Обновляем цвет таймера
        this.updateTimerColor(seconds);
    }

    // Обновление цвета таймера
    updateTimerColor(seconds) {
        const timerElement = document.getElementById('fight-timer');
        if (!timerElement) return;

        timerElement.classList.remove('timer-normal', 'timer-warning', 'timer-critical');

        if (seconds > 60) {
            timerElement.classList.add('timer-normal');
        } else if (seconds > 10) {
            timerElement.classList.add('timer-warning');
        } else {
            timerElement.classList.add('timer-critical');
        }
    }

    // Установка времени таймера
    async setTimer(fightId, seconds) {
        try {
            const response = await fetch(`/referee/api/update_timer/${fightId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ seconds })
            });

            const data = await response.json();

            if (data.success) {
                this.refreshFightStatus();
            } else {
                JudoSystem.showNotification(data.error || 'Ошибка', 'danger');
            }
        } catch (error) {
            console.error('Timer set error:', error);
        }
    }

    // Сброс таймера
    async resetTimer(fightId) {
        const fightDuration = 300; // 5 минут
        await this.setTimer(fightId, fightDuration);
    }

    // Переход в золотой скор
    enterGoldenScore() {
        const timerElement = document.getElementById('fight-timer');
        if (timerElement) {
            timerElement.classList.add('golden');
            JudoSystem.showNotification('Золотой скор!', 'warning');
        }
    }

    // Обновление таймера на сервере
    async updateServerTimer(seconds) {
        if (!this.currentFightId) return;

        try {
            await fetch(`/referee/api/update_timer/${this.currentFightId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ seconds })
            });
        } catch (error) {
            console.error('Server timer update error:', error);
        }
    }

    // Обновление статуса схватки
    async refreshFightStatus() {
        if (!this.currentFightId) return;

        try {
            const response = await fetch(`/referee/api/fight_status/${this.currentFightId}`);
            const fightStatus = await response.json();

            this.updateFightDisplay(fightStatus);
        } catch (error) {
            console.error('Status refresh error:', error);
        }
    }

    // Обновление отображения схватки
    updateFightDisplay(fightStatus) {
        // Обновляем счет
        if (fightStatus.scores) {
            this.updateScores(fightStatus.scores);
        }

        // Обновляем штрафы
        if (fightStatus.penalties) {
            this.updatePenalties(fightStatus.penalties);
        }

        // Обновляем таймер
        if (fightStatus.timer_seconds !== undefined) {
            this.updateTimer(fightStatus.timer_seconds);
        }

        // Обновляем статус
        this.updateStatus(fightStatus.status);
    }

    // Обновление счета
    updateScores(scores) {
        const whiteScore = document.querySelector('[data-athlete="white"] [data-score-display]');
        const blueScore = document.querySelector('[data-athlete="blue"] [data-score-display]');

        if (whiteScore) whiteScore.textContent = scores.white || 0;
        if (blueScore) blueScore.textContent = scores.blue || 0;
    }

    // Обновление штрафов
    updatePenalties(penalties) {
        this.updatePenaltyDots('white', penalties.white);
        this.updatePenaltyDots('blue', penalties.blue);
    }

    // Обновление точек штрафов
    updatePenaltyDots(athleteColor, penaltyCount) {
        const container = document.querySelector(`[data-athlete="${athleteColor}"] [data-penalties]`);
        if (!container) return;

        container.innerHTML = '';

        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = `penalty-dot ${i < penaltyCount ? 'active' : ''}`;
            container.appendChild(dot);
        }
    }

    // Обновление таймера
    updateTimer(seconds) {
        const secondsElement = document.getElementById('timer-seconds');
        if (secondsElement) {
            secondsElement.textContent = seconds;
        }
    }

    // Обновление статуса
    updateStatus(status) {
        const statusElement = document.getElementById('fight-status');
        if (statusElement) {
            statusElement.textContent = this.getStatusText(status);
            statusElement.className = `status-badge status-${status.toLowerCase()}`;
        }
    }

    // Получение текста статуса
    getStatusText(status) {
        const statusMap = {
            'SCHEDULED': 'Запланирована',
            'LIVE': 'В процессе',
            'COMPLETED': 'Завершена',
            'CANCELLED': 'Отменена'
        };

        return statusMap[status] || status;
    }

    // Авто-обновление
    startAutoRefresh() {
        this.autoRefreshInterval = setInterval(() => {
            this.refreshFightStatus();
        }, 3000); // Обновление каждые 3 секунды
    }

    // Остановка авто-обновления
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }

    // Обработка горячих клавиш
    handleHotkeys(event) {
        if (event.ctrlKey || event.altKey) return;

        switch (event.key) {
            case '1':
                document.querySelector('[data-score-action][data-athlete-color="white"][data-score-type="IPPON"]')?.click();
                break;

            case '2':
                document.querySelector('[data-score-action][data-athlete-color="white"][data-score-type="WAZAARI"]')?.click();
                break;

            case '3':
                document.querySelector('[data-score-action][data-athlete-color="white"][data-score-type="SHIDO"]')?.click();
                break;

            case '7':
                document.querySelector('[data-score-action][data-athlete-color="blue"][data-score-type="IPPON"]')?.click();
                break;

            case '8':
                document.querySelector('[data-score-action][data-athlete-color="blue"][data-score-type="WAZAARI"]')?.click();
                break;

            case '9':
                document.querySelector('[data-score-action][data-athlete-color="blue"][data-score-type="SHIDO"]')?.click();
                break;

            case ' ':
                event.preventDefault();
                this.toggleTimer();
                break;

            case 'Enter':
                event.preventDefault();
                document.querySelector('[data-fight-action="complete"]')?.click();
                break;
        }
    }

    // Переключение таймера (пауза/возобновление)
    toggleTimer() {
        const pauseBtn = document.querySelector('[data-fight-action="pause"]');
        const resumeBtn = document.querySelector('[data-fight-action="resume"]');

        if (pauseBtn && !pauseBtn.disabled) {
            pauseBtn.click();
        } else if (resumeBtn && !resumeBtn.disabled) {
            resumeBtn.click();
        }
    }

    // Полноэкранный режим
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
    }

    // Установка текущей схватки
    setCurrentFight(fightId) {
        this.currentFightId = fightId;
        this.refreshFightStatus();
    }

    // Очистка при уничтожении
    destroy() {
        this.stopAutoRefresh();

        if (this.timerInterval) {
            clearInterval(this.timerInterval);
        }

        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.refereeInterface = new RefereeInterface();
});

// Глобальные функции для использования в HTML
function setCurrentFight(fightId) {
    if (window.refereeInterface) {
        window.refereeInterface.setCurrentFight(fightId);
    }
}

function toggleFullscreen() {
    if (window.refereeInterface) {
        window.refereeInterface.toggleFullscreen();
    }
}