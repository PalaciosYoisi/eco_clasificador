// =============================================
// 1. CONFIGURACIÓN DE LA API Y CONSTANTES
// =============================================
const API_BASE_URL = 'http://127.0.0.1:5000'; // URL de tu API Flask
const MAX_FILE_SIZE_MB = 10;

// Elementos del Clasificador
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('preview-container');
const imagePreview = document.getElementById('image-preview');
const analyzeBtn = document.getElementById('analyze-btn');
const resetBtn = document.getElementById('reset-btn');
const analyzeText = document.getElementById('analyze-text');
const analyzeLoading = document.getElementById('analyze-loading');
const resultContainer = document.getElementById('result-container');
const wasteType = document.getElementById('waste-type');
const wasteInfo = document.getElementById('waste-info');
const disposalInfo = document.getElementById('disposal-info');

let currentFile = null;

// Elementos del Chatbot
const chatbotButton = document.getElementById('chatbot-button');
const chatbotWindow = document.getElementById('chatbot-window');
const closeChatbot = document.getElementById('close-chatbot');
const chatbotMessages = document.getElementById('chatbot-messages');
const initialMenu = document.getElementById('initial-menu');

// Elementos del Menú de Navegación para scroll suave
const navLinks = document.querySelectorAll('a[href^="#"]');

// =============================================
// 2. FUNCIONES DE UTILIDAD Y CORE
// =============================================

/**
 * Muestra una notificación temporal
 * @param {string} message - Mensaje a mostrar.
 * @param {string} type - Tipo de mensaje ('success', 'error', 'info').
 */
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    notification.style.cssText = `
        position: fixed;
        top: 90px;
        right: 20px;
        max-width: min(380px, calc(100vw - 40px));
        padding: 14px 20px;
        border-radius: 16px;
        color: white;
        font-family: 'DM Sans', 'Segoe UI', sans-serif;
        font-weight: 600;
        font-size: .93rem;
        z-index: 10000;
        box-shadow: 0 20px 40px -12px rgba(12,36,23,.45);
        opacity: 0;
        transition: opacity .5s, transform .6s cubic-bezier(.22,1,.36,1);
        transform: translateX(40px);
    `;

    if (type === 'error') notification.style.backgroundColor = '#c62828';
    if (type === 'success') notification.style.backgroundColor = '#1f7a3a';
    if (type === 'info') notification.style.backgroundColor = '#0c2417';

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateX(0)';
    }, 10);

    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(40px)';
        notification.addEventListener('transitionend', () => notification.remove());
    }, 4000);
}

/**
 * Muestra la vista previa de la imagen cargada y el botón de análisis.
 * @param {File} file - El archivo de imagen a previsualizar.
 */
function displayImagePreview(file) {
    if (!file.type.startsWith('image/')) {
        showNotification('El archivo seleccionado no es una imagen.', 'error');
        return;
    }

    if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
        showNotification(`La imagen es demasiado grande. Máximo ${MAX_FILE_SIZE_MB}MB.`, 'error');
        return;
    }

    currentFile = file;

    const reader = new FileReader();
    reader.onload = function(e) {
        imagePreview.src = e.target.result;
        imagePreview.alt = file.name;

        // Ocultar área de carga
        uploadArea.style.display = 'none';

        // Mostrar contenedor de vista previa con animación
        previewContainer.style.display = 'block';
        setTimeout(() => {
            previewContainer.style.opacity = '1';
            resultContainer.style.display = 'none'; // Ocultar resultados anteriores
        }, 10);

        // Activar botón de análisis
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

/**
 * Restaura la interfaz a su estado inicial.
 */
function resetClassifier() {
    currentFile = null;
    fileInput.value = '';

    previewContainer.style.opacity = '0';
    previewContainer.style.display = 'none';

    resultContainer.style.opacity = '0';
    resultContainer.style.display = 'none';

    uploadArea.style.display = 'block';
    analyzeBtn.disabled = true;
}

// =============================================
// 3. LÓGICA DE CLASIFICADOR (IA)
// =============================================

/**
 * Maneja el envío de la imagen a la API para clasificación.
 */
async function handleAnalyze() {
    if (!currentFile) {
        showNotification('Por favor, primero carga una imagen.', 'info');
        return;
    }

    // 1. Mostrar estado de carga
    analyzeText.textContent = 'Analizando...';
    analyzeLoading.style.display = 'inline-block';
    analyzeBtn.disabled = true;

    // 2. Preparar FormData
    const formData = new FormData();
    // 🚨 FIX: Cambiado 'file' a 'imagen' para que coincida con app.py (request.files['imagen'])
    formData.append('imagen', currentFile);

    try {
        // 3. Petición a la API
        const response = await fetch(`${API_BASE_URL}/clasificar`, {
            method: 'POST',
            body: formData
        });

        // Manejo de errores HTTP
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.mensaje || `Error HTTP: ${response.status}`);
        }

        // 4. Procesar respuesta exitosa
        const data = await response.json();

        if (data.estado === 'error') {
             throw new Error(data.mensaje || 'Error desconocido al clasificar.');
        }

        // Obtener el tipo de residuo y la confianza
        const categoria = data.categoria || 'Desconocida';
        const confianza = (data.confianza * 100).toFixed(2);

        // Usamos la información de guía_residuo que devuelve la API
        const guia = data.guia_residuo || {};

        // Formatear el resultado
        const htmlInfo = `
            <p><strong>Nivel de Confianza:</strong> <span style="color: ${confianza > 80 ? 'var(--primary-color)' : '#ff9800'}; font-weight: bold;">${confianza}%</span></p>
            <div class="conf-meter"><span style="width: ${Math.min(confianza, 100)}%"></span></div>
            <p>La IA ha determinado esta categoría. Puedes encontrar su destino más abajo.</p>
        `;

        const htmlDisposal = `
            <p><strong>Contenedor Recomendado:</strong> <span style="font-weight: bold; color: var(--secondary-color);">${guia.contenedor_color || 'N/A'} (${guia.contenedor_nombre || 'Contenedor Especial'})</span></p>
            <p><strong>Instrucciones:</strong> ${guia.instrucciones || 'Separar cuidadosamente y llevar al punto de recolección más cercano.'}</p>
            <p><strong>Ejemplos:</strong> ${guia.ejemplos || 'No disponibles'}</p>
        `;

        // 5. Actualizar la interfaz de resultados
        wasteType.textContent = `¡Clasificación Exitosa! (${categoria})`;
        wasteInfo.innerHTML = htmlInfo;
        disposalInfo.innerHTML = htmlDisposal;

        // Mostrar el contenedor de resultados
        resultContainer.style.display = 'block';
        setTimeout(() => {
            resultContainer.style.opacity = '1';
            // Desplazar a resultados
            resultContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 10);

        showNotification(`Residuo clasificado como: ${categoria}`, 'success');

    } catch (error) {
        console.error('Error al analizar la imagen:', error);

        wasteType.textContent = "Error en el análisis";
        wasteInfo.innerHTML = `<p style="color: #c62828;"><i class="fas fa-exclamation-triangle"></i> ${error.message}</p>`;
        disposalInfo.innerHTML = "Por favor, intenta con otra imagen o verifica que la API esté corriendo en la URL configurada.";

        // Mostrar error en el contenedor de resultados
        resultContainer.style.display = 'block';
        setTimeout(() => resultContainer.style.opacity = '1', 10);

        showNotification('Falló la clasificación. Revisa la consola para detalles.', 'error');

    } finally {
        // 6. Restaurar estado del botón
        analyzeText.textContent = 'Analizar con IA';
        analyzeLoading.style.display = 'none';
        analyzeBtn.disabled = false;
    }
}

// =============================================
// 4. LÓGICA DEL CHATBOT DE MENÚ
// =============================================

/**
 * Crea un mensaje en el área de conversación del chatbot.
 * @param {string} text - Contenido del mensaje.
 * @param {string} sender - 'bot' o 'user'.
 */
function createMessage(text, sender) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${sender}-message`;

    // Manejar saltos de línea para un mejor formato
    messageElement.innerHTML = text.replace(/\n/g, '<br>');

    chatbotMessages.appendChild(messageElement);
    // Scroll automático hacia el final
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;

    return messageElement;
}

/**
 * Muestra las opciones de menú en el chatbot y oculta el contenido anterior.
 * @param {HTMLElement} menuContainer - El contenedor de las opciones (e.g., initialMenu).
 */
function showMenuOptions(menuContainer) {
    // Ocultar todas las opciones previas (si existen)
    const existingMenus = chatbotMessages.querySelectorAll('.menu-options');
    existingMenus.forEach(menu => menu.style.display = 'none');

    // Mostrar el menú actual
    menuContainer.style.display = 'flex';
    chatbotMessages.appendChild(menuContainer);
    chatbotMessages.scrollTop = chatbotMessages.scrollHeight;
}

/**
 * Desactiva temporalmente los botones del menú.
 */
function disableMenuButtons() {
    const buttons = chatbotMessages.querySelectorAll('.menu-options .menu-btn');
    buttons.forEach(btn => btn.disabled = true);
}

/**
 * Activa los botones del menú.
 */
function enableMenuButtons() {
    const buttons = chatbotMessages.querySelectorAll('.menu-options .menu-btn');
    buttons.forEach(btn => btn.disabled = false);
}

/**
 * Maneja la selección de una opción de menú y llama a la API.
 * @param {Event} event - Evento de click.
 */
async function handleMenuClick(event) {
    const btn = event.target.closest('.menu-btn');
    if (!btn || btn.disabled) return;

    const endpoint = btn.getAttribute('data-endpoint');
    const text = btn.textContent;
    const type = btn.getAttribute('data-type'); // 'guia', 'consejo', 'centros'

    // 1. Mostrar mensaje del usuario y deshabilitar botones
    createMessage(text, 'user');
    disableMenuButtons();

    // 2. Mostrar mensaje de carga del bot
    const loadingMessage = createMessage('<div class="loading"></div> Buscando información...', 'bot');

    try {
        // 3. Petición a la API
        const response = await fetch(`${API_BASE_URL}${endpoint}`);

        // 4. Manejo de errores
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.mensaje || `Error en la API: ${response.status}`);
        }

        const data = await response.json();
        let botResponseText = '';

        // 5. Formatear la respuesta según el tipo de endpoint
        if (type === 'guia') {
            // Endpoint /guias/<nombre_residuo>
            botResponseText = `♻️ Guía de ${data.residuo || 'Residuo'}:\n\nContenedor: ${data.contenedor_color || 'N/A'}\nInstrucciones: ${data.instrucciones || 'N/A'}\n\nResiduos Comunes: ${data.residuos_ejemplo.join(', ')}`;
        } else if (type === 'consejo') {
            // Endpoint /consejos/<slug_consejo>
            botResponseText = `💡 ${data.titulo}\n\n${data.contenido}\n\nFecha: ${data.fecha}`;
        } else if (type === 'centros') {
            // Endpoint /centros-reciclaje
            const centros = data.centros || [];
            if (centros.length > 0) {
                botResponseText = '📍 Puntos de Reciclaje en Quibdó:\n';
                centros.slice(0, 3).forEach(c => { // Mostrar solo 3 para no saturar
                    botResponseText += `\n- ${c.nombre} (${c.tipo})\n  Dir: ${c.direccion}\n  Contacto: ${c.telefono || 'N/A'}`;
                });
                if (centros.length > 3) {
                     botResponseText += `\n\n...y ${centros.length - 3} más. Consulta la API para ver la lista completa.`;
                }
            } else {
                botResponseText = 'No se encontraron centros de reciclaje activos en este momento.';
            }
        } else {
            botResponseText = 'Respuesta de la API recibida. ¡Pero el formato es desconocido!';
        }

        // Eliminar mensaje de carga y mostrar respuesta final
        loadingMessage.remove();
        createMessage(botResponseText, 'bot');

    } catch (error) {
        console.error('Error del EcoBot al contactar la API:', error);
        // Eliminar mensaje de carga y mostrar error
        loadingMessage.remove();
        createMessage(`❌ Error: No pude obtener la información. El servidor API podría estar apagado o el endpoint falló. Detalles: ${error.message}`, 'bot');
    } finally {
        // 6. Devolver al menú principal después de un breve retraso
        setTimeout(() => {
            createMessage('¿Necesitas algo más? Selecciona una opción del menú.', 'bot');
            showMenuOptions(initialMenu);
            enableMenuButtons();
        }, 1000);
    }
}

// =============================================
// 5. LISTENERS Y ENLACES
// =============================================

document.addEventListener('DOMContentLoaded', () => {
    // 5.1 Listeners del Clasificador

    // Listener para Clic en el área de carga
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); }
    });

    // Listener para la selección del archivo
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            displayImagePreview(e.target.files[0]);
        }
    });

    // Listener para Drag and Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false); // Prevenir acción por defecto del navegador
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    // Resaltar área de carga al arrastrar sobre ella
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
    });

    // Manejo de Soltar (Drop)
    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            displayImagePreview(files[0]);
        }
    }, false);

    // Listener para Pegar (Paste)
    document.addEventListener('paste', (e) => {
        const items = e.clipboardData.items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') !== -1) {
                const file = items[i].getAsFile();
                if (file) {
                    displayImagePreview(file);
                    showNotification('Imagen pegada desde el portapapeles. ¡Lista para analizar!', 'info');
                }
                return; // Solo procesar la primera imagen
            }
        }
    });

    // Listener para el botón de analizar
    analyzeBtn.addEventListener('click', handleAnalyze);
    resetBtn.addEventListener('click', resetClassifier);

    // 5.2 Listeners del Chatbot

    // Abrir/Cerrar la ventana del chatbot
    const toggleChat = () => {
        chatbotWindow.style.display = (chatbotWindow.style.display === 'flex' ? 'none' : 'flex');
    };
    chatbotButton.addEventListener('click', toggleChat);
    chatbotButton.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggleChat(); }
    });

    closeChatbot.addEventListener('click', () => {
        chatbotWindow.style.display = 'none';
    });

    // Listener para los botones del menú (Delegación)
    initialMenu.addEventListener('click', handleMenuClick);

    // 5.3 Listener para scroll suave en enlaces de navegación
    const mainNav = document.getElementById('main-nav');
    const menuToggle = document.getElementById('menu-toggle');

    navLinks.forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start' // Asegura que la sección quede en la parte superior
                });
            }
            mainNav.classList.remove('open');
            menuToggle.setAttribute('aria-expanded', 'false');
        });
    });

    // 5.4 Comprobación inicial de la API
    checkAPIStatus();

    // Comprobación periódica (cada 30 segundos)
    setInterval(checkAPIStatus, 30000);

    // 5.5 Efectos visuales de la página
    initVisualEffects(mainNav, menuToggle);
});

/**
 * Verifica si la API está en línea (Endpoint /)
 */
async function checkAPIStatus() {
    try {
        const response = await fetch(API_BASE_URL);
        if (response.ok) {
            console.log('✅ API de EcoClasificador está activa.');
        } else {
            console.error('⚠️ API de EcoClasificador en línea pero respondió con error.');
        }
    } catch (error) {
        console.error('❌ No se pudo conectar a la API. Asegúrate de que el servidor Flask esté corriendo.', error.message);
    }
}

// =============================================
// 6. EFECTOS VISUALES (solo presentación)
// =============================================
function initVisualEffects(mainNav, menuToggle) {
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Menú móvil
    menuToggle.addEventListener('click', () => {
        const open = mainNav.classList.toggle('open');
        menuToggle.setAttribute('aria-expanded', open);
    });

    // Header compacto + barra de progreso
    const header = document.getElementById('site-header');
    const progress = document.getElementById('scroll-progress');
    const onScroll = () => {
        const y = window.scrollY;
        header.classList.toggle('scrolled', y > 40);
        const max = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    // Aparición al hacer scroll (con escalonado entre hermanos)
    const reveals = document.querySelectorAll('.reveal');
    reveals.forEach(el => {
        const idx = Array.prototype.indexOf.call(el.parentElement.children, el);
        el.style.transitionDelay = `${Math.min(idx, 6) * 90}ms`;
    });
    const revealObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('in');
                revealObs.unobserve(entry.target);
                // Quitar el retraso tras la entrada para que el hover sea instantáneo
                setTimeout(() => { entry.target.style.transitionDelay = ''; }, 1200);
            }
        });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    reveals.forEach(el => revealObs.observe(el));

    // Contadores animados
    const animateCount = (el) => {
        const target = parseFloat(el.dataset.count);
        const prefix = el.dataset.prefix || '';
        const suffix = el.dataset.suffix || '';
        if (reduceMotion) { el.textContent = prefix + target + suffix; return; }
        const duration = 1600;
        const start = performance.now();
        const tick = (now) => {
            const t = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - t, 4);
            el.textContent = prefix + Math.round(target * eased) + suffix;
            if (t < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
    };
    const countObs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) { animateCount(entry.target); countObs.unobserve(entry.target); }
        });
    }, { threshold: 0.6 });
    document.querySelectorAll('[data-count]').forEach(el => countObs.observe(el));

    // Enlace activo según la sección visible
    const sections = ['inicio', 'mision', 'clasificador', 'guia', 'consejos']
        .map(id => document.getElementById(id)).filter(Boolean);
    const navAnchors = mainNav.querySelectorAll('a');
    const spy = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navAnchors.forEach(a => a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id));
            }
        });
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach(s => spy.observe(s));

    // Foco de luz que sigue al cursor en las tarjetas
    document.querySelectorAll('.spot').forEach(card => {
        card.addEventListener('pointermove', (e) => {
            const r = card.getBoundingClientRect();
            card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
            card.style.setProperty('--my', (e.clientY - r.top) + 'px');
        });
    });

    // Demo del hero: barra de confianza ilustrativa
    const demoMeter = document.getElementById('demo-meter');
    const demoPct = document.getElementById('demo-pct');
    const runDemo = () => {
        demoMeter.style.width = '96%';
        let n = 0;
        const id = setInterval(() => {
            n += 3;
            if (n >= 96) { n = 96; clearInterval(id); }
            demoPct.textContent = n + '%';
        }, 28);
    };
    setTimeout(runDemo, 900);

    // Inclinación 3D suave de la tarjeta del hero
    const scanCard = document.getElementById('scan-card');
    if (scanCard && !reduceMotion && window.matchMedia('(hover: hover)').matches) {
        const hero = document.getElementById('inicio');
        hero.addEventListener('pointermove', (e) => {
            const r = hero.getBoundingClientRect();
            const x = (e.clientX - r.left) / r.width - 0.5;
            const y = (e.clientY - r.top) / r.height - 0.5;
            scanCard.style.transform = `rotateY(${x * 10}deg) rotateX(${-y * 8}deg)`;
        });
        hero.addEventListener('pointerleave', () => { scanCard.style.transform = ''; });
    }
}
