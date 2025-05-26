// Utilitários globais da aplicação
class EsporteSocialApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupNotifications();
        this.setupLocationTracking();
        this.setupRealTimeUpdates();
        this.setupFormValidation();
        this.setupAnimations();
    }

    // Sistema de notificações
    setupNotifications() {
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = 'notification-container';
        document.body.appendChild(this.notificationContainer);
    }

    showNotification(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span>${message}</span>
                <button type="button" class="btn-close btn-close-white ms-3" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
        `;

        this.notificationContainer.appendChild(notification);

        // Animar entrada
        setTimeout(() => notification.classList.add('show'), 100);

        // Auto-remover
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    // Rastreamento de localização
    setupLocationTracking() {
        this.currentLocation = null;
        this.watchLocationId = null;
    }

    getCurrentLocation() {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject(new Error('Geolocalização não suportada'));
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.currentLocation = {
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude
                    };
                    resolve(this.currentLocation);
                },
                (error) => {
                    let message = 'Erro ao obter localização';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Permissão de localização negada';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Localização indisponível';
                            break;
                        case error.TIMEOUT:
                            message = 'Timeout ao obter localização';
                            break;
                    }
                    reject(new Error(message));
                },
                { timeout: 10000, enableHighAccuracy: true }
            );
        });
    }

    // Atualizações em tempo real
    setupRealTimeUpdates() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupSocketEvents();
        }
    }

    setupSocketEvents() {
        this.socket.on('connect', () => {
            console.log('Conectado ao servidor');
        });

        this.socket.on('disconnect', () => {
            console.log('Desconectado do servidor');
            this.showNotification('Conexão perdida. Tentando reconectar...', 'warning');
        });

        this.socket.on('match_update', (data) => {
            this.handleMatchUpdate(data);
        });

        this.socket.on('user_notification', (data) => {
            this.showNotification(data.message, data.type);
        });
    }

    handleMatchUpdate(data) {
        // Atualizar dados do jogo na interface
        const matchElement = document.querySelector(`[data-match-id="${data.match_id}"]`);
        if (matchElement) {
            this.updateMatchElement(matchElement, data);
        }
    }

    updateMatchElement(element, data) {
        // Atualizar placar
        const homeScore = element.querySelector('.home-score');
        const awayScore = element.querySelector('.away-score');
        const status = element.querySelector('.match-status');

        if (homeScore) homeScore.textContent = data.home_score;
        if (awayScore) awayScore.textContent = data.away_score;
        if (status) status.textContent = data.status;

        // Adicionar animação de atualização
        element.classList.add('animate-pulse');
        setTimeout(() => element.classList.remove('animate-pulse'), 2000);
    }

    // Validação de formulários
    setupFormValidation() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.classList.contains('needs-validation')) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                    this.showValidationErrors(form);
                }
                form.classList.add('was-validated');
            }
        });
    }

    showValidationErrors(form) {
        const invalidElements = form.querySelectorAll(':invalid');
        invalidElements.forEach(element => {
            const feedback = element.parentElement.querySelector('.invalid-feedback');
            if (feedback) {
                feedback.style.display = 'block';
            }
        });
    }

    // Animações
    setupAnimations() {
        // Intersection Observer para animações de entrada
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                }
            });
        });

        // Observar elementos com classe animate-on-scroll
        document.querySelectorAll('.animate-on-scroll').forEach(el => {
            observer.observe(el);
        });
    }

    // Utilitários para requisições AJAX
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Erro na requisição');
            }

            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            this.showNotification(error.message, 'error');
            throw error;
        }
    }

    // Cache simples
    cache = new Map();

    setCache(key, value, ttl = 300000) { // 5 minutos default
        this.cache.set(key, {
            value,
            expires: Date.now() + ttl
        });
    }

    getCache(key) {
        const item = this.cache.get(key);
        if (!item) return null;
        
        if (Date.now() > item.expires) {
            this.cache.delete(key);
            return null;
        }
        
        return item.value;
    }

    // Formatação de data/hora
    formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('pt-BR');
    }

    formatTime(dateString) {
        return new Date(dateString).toLocaleTimeString('pt-BR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Utilitário para debounce
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Inicializar aplicação
const app = new EsporteSocialApp();

// Expor globalmente para uso em templates
window.EsporteSocialApp = app;

// Função global para mostrar loading nos botões
function setButtonLoading(button, loading = true) {
    if (loading) {
        button.classList.add('btn-loading');
        button.disabled = true;
    } else {
        button.classList.remove('btn-loading');
        button.disabled = false;
    }
}

// Service Worker para PWA (básico)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then(registration => {
                console.log('SW registrado com sucesso:', registration);
            })
            .catch(registrationError => {
                console.log('SW falhou ao registrar:', registrationError);
            });
    });
}