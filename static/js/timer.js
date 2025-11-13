/**
 * Таймер для схваток дзюдо
 */

class JudoTimer {
    constructor(options = {}) {
        this.defaults = {
            duration: 300, // 5 минут в секундах
            goldenScoreDuration: 180, // 3 минуты золотой скор
            updateInterval: 1000, // Обновление каждую секунду
            onTick: null,
            onTimeout: null,
            onGoldenScore: null
        };

        this.settings = { ...this.defaults, ...options };

        this.seconds = this.settings.duration;
        this.isRunning = false;
        this.isPaused = false;
        this.isGoldenScore = false;
        this.intervalId = null;

        this.initialize();
    }

    initialize() {
        this.bindEvents();
        this.updateDisplay();
    }

    bindEvents() {
        // События будут обрабатываться через публичные методы
    }

    // Запуск таймера
    start() {
        if (this.isRunning) return;

        this.isRunning = true;
        this.isPaused = false;

        this.intervalId = setInterval(() => {
            this.tick();
        }, this.settings.updateInterval);

        this.onStateChange('started');
    }

    // Пауза таймера
    pause() {
        if (!this.isRunning || this.isPaused) return;

        this.isPaused = true;
        this.onStateChange('paused');
    }

    // Возобновление таймера
    resume() {
        if (!this.isRunning || !this.isPaused) return;

        this.isPaused = false;
        this.onStateChange('resumed');
    }

    // Остановка таймера
    stop() {
        this.isRunning = false;
        this.isPaused = false;

        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }

        this.onStateChange('stopped');
    }

    // Сброс таймера
    reset() {
        this.stop();
        this.seconds = this.isGoldenScore ? this.settings.goldenScoreDuration : this.settings.duration;
        this.isGoldenScore = false;
        this.updateDisplay();
        this.onStateChange('reset');
    }

    // Установка времени
    setTime(seconds) {
        this.seconds = Math.max(0, seconds);
        this.updateDisplay();
    }

    // Тик таймера
    tick() {
        if (this.isPaused || !this.isRunning) return;

        if (this.seconds > 0) {
            this.seconds--;
            this.updateDisplay();
            this.onTick();

            // Проверка перехода в золотой скор
            if (this.seconds === 0 && !this.isGoldenScore) {
                this.enterGoldenScore();
            }
        } else {
            this.onTimeout();
            this.stop();
        }
    }

    // Переход в золотой скор
    enterGoldenScore() {
        this.isGoldenScore = true;
        this.seconds = this.settings.goldenScoreDuration;
        this.onGoldenScore();
    }

    // Обновление отображения
    updateDisplay() {
        const displayElement = document.getElementById(this.settings.displayElement);
        if (!displayElement) return;

        const minutes = Math.floor(this.seconds / 60);
        const seconds = this.seconds % 60;
        const formattedTime = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

        displayElement.textContent = formattedTime;

        // Обновление классов для визуальных эффектов
        this.updateDisplayClasses(displayElement);
    }

    // Обновление классов отображения
    updateDisplayClasses(displayElement) {
        // Удаляем предыдущие классы
        displayElement.classList.remove('timer-normal', 'timer-warning', 'timer-critical', 'timer-golden');

        // Добавляем соответствующие классы
        if (this.isGoldenScore) {
            displayElement.classList.add('timer-golden');
        } else if (this.seconds > 60) {
            displayElement.classList.add('timer-normal');
        } else if (this.seconds > 10) {
            displayElement.classList.add('timer-warning');
        } else {
            displayElement.classList.add('timer-critical');
        }

        // Добавляем класс паузы если нужно
        if (this.isPaused) {
            displayElement.classList.add('timer-paused');
        } else {
            displayElement.classList.remove('timer-paused');
        }
    }

    // Обработчики событий
    onTick() {
        if (typeof this.settings.onTick === 'function') {
            this.settings.onTick(this.seconds, this.isGoldenScore);
        }
    }

    onTimeout() {
        if (typeof this.settings.onTimeout === 'function') {
            this.settings.onTimeout(this.isGoldenScore);
        }
    }

    onGoldenScore() {
        if (typeof this.settings.onGoldenScore === 'function') {
            this.settings.onGoldenScore();
        }
    }

    onStateChange(state) {
        // Можно добавить кастомные обработчики для разных состояний
        console.log(`Timer ${state}: ${this.seconds}s remaining`);
    }

    // Получение текущего состояния
    getState() {
        return {
            seconds: this.seconds,
            isRunning: this.isRunning,
            isPaused: this.isPaused,
            isGoldenScore: this.isGoldenScore,
            formattedTime: this.getFormattedTime()
        };
    }

    // Получение форматированного времени
    getFormattedTime() {
        const minutes = Math.floor(this.seconds / 60);
        const seconds = this.seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    // Уничтожение таймера
    destroy() {
        this.stop();
    }
}

// Глобальный экземпляр таймера
window.judoTimer = null;

// Функция инициализации таймера
function initializeJudoTimer(options = {}) {
    if (window.judoTimer) {
        window.judoTimer.destroy();
    }

    window.judoTimer = new JudoTimer(options);
    return window.judoTimer;
}

// Глобальные функции управления таймером
function startTimer() {
    if (window.judoTimer) {
        window.judoTimer.start();
    }
}

function pauseTimer() {
    if (window.judoTimer) {
        window.judoTimer.pause();
    }
}

function resumeTimer() {
    if (window.judoTimer) {
        window.judoTimer.resume();
    }
}

function stopTimer() {
    if (window.judoTimer) {
        window.judoTimer.stop();
    }
}

function resetTimer() {
    if (window.judoTimer) {
        window.judoTimer.reset();
    }
}

function setTimerTime(seconds) {
    if (window.judoTimer) {
        window.judoTimer.setTime(seconds);
    }
}

// Автоматическая инициализация при наличии элемента таймера
document.addEventListener('DOMContentLoaded', function() {
    const timerElement = document.getElementById('judo-timer');

    if (timerElement) {
        const duration = parseInt(timerElement.getAttribute('data-duration')) || 300;
        const goldenScoreDuration = parseInt(timerElement.getAttribute('data-golden-score-duration')) || 180;

        initializeJudoTimer({
            displayElement: 'judo-timer',
            duration: duration,
            goldenScoreDuration: goldenScoreDuration,
            onTick: function(seconds, isGoldenScore) {
                // Дополнительные действия при каждом тике
                updateTimerProgress(seconds, duration, isGoldenScore);
            },
            onTimeout: function(isGoldenScore) {
                JudoSystem.showNotification(isGoldenScore ? 'Время золотого скора вышло!' : 'Время схватки вышло!', 'warning');
            },
            onGoldenScore: function() {
                JudoSystem.showNotification('Золотой скор!', 'info');
                playSound('golden_score');
            }
        });
    }
});

// Обновление прогресс-бара таймера
function updateTimerProgress(currentSeconds, totalSeconds, isGoldenScore) {
    const progressElement = document.getElementById('timer-progress');
    if (!progressElement) return;

    const percentage = (currentSeconds / totalSeconds) * 100;
    progressElement.style.width = percentage + '%';

    // Обновление цвета прогресс-бара
    progressElement.classList.remove('bg-success', 'bg-warning', 'bg-danger', 'bg-info');

    if (isGoldenScore) {
        progressElement.classList.add('bg-info');
    } else if (percentage > 50) {
        progressElement.classList.add('bg-success');
    } else if (percentage > 20) {
        progressElement.classList.add('bg-warning');
    } else {
        progressElement.classList.add('bg-danger');
    }
}

// Воспроизведение звуков
function playSound(soundType) {
    // В реальном приложении здесь будет воспроизведение звуковых файлов
    console.log('Playing sound:', soundType);

    // Пример использования Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        switch (soundType) {
            case 'start':
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                break;
            case 'pause':
                oscillator.frequency.setValueAtTime(400, audioContext.currentTime);
                break;
            case 'golden_score':
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
                break;
            case 'timeout':
                oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
                break;
            default:
                oscillator.frequency.setValueAtTime(500, audioContext.currentTime);
        }

        gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1);

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 1);

    } catch (error) {
        console.warn('Web Audio API not supported:', error);
    }
}

// Утилиты для работы со временем
const TimerUtils = {
    // Преобразование времени в секунды
    timeToSeconds(timeString) {
        const parts = timeString.split(':');
        if (parts.length === 2) {
            return parseInt(parts[0]) * 60 + parseInt(parts[1]);
        }
        return 0;
    },

    // Преобразование секунд в формат MM:SS
    secondsToTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },

    // Форматирование времени для отображения
    formatDisplayTime(seconds, showMilliseconds = false) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;

        if (showMilliseconds) {
            const ms = Math.floor((seconds - Math.floor(seconds)) * 100);
            return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
        }

        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    },

    // Создание обратного отсчета
    createCountdown(duration, onTick, onComplete) {
        let remaining = duration;
        const interval = setInterval(() => {
            remaining--;

            if (onTick) {
                onTick(remaining);
            }

            if (remaining <= 0) {
                clearInterval(interval);
                if (onComplete) {
                    onComplete();
                }
            }
        }, 1000);

        return {
            stop: function() {
                clearInterval(interval);
            },
            getRemaining: function() {
                return remaining;
            }
        };
    }
};

// Экспорт утилит
window.TimerUtils = TimerUtils;