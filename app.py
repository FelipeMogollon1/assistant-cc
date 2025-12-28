from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# =============================================================================
# CONFIGURACIÓN DE IA (Groq API - Gratuita y rápida)
# =============================================================================
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')  # Obtener clave de .env
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Base de conocimiento de la Cámara de Comercio
CONOCIMIENTO_CCP = """
Eres un asistente virtual de la Cámara de Comercio de Pereira por Risaralda.

INFORMACIÓN CLAVE:
- La Cámara fue fundada en 1926
- Es una entidad privada sin ánimo de lucro
- Presta servicios de Registros Públicos

SERVICIOS PRINCIPALES:
1. Renovación de Matrícula Mercantil
   - Fecha límite: 31 de marzo de cada año
   - Se puede hacer en línea o presencial
   - Costo varía según activos de la empresa

2. Registro de Empresas
   - Persona Natural o Jurídica
   - Requiere: RUT, Formulario de registro, Documento de identidad

3. Certificados
   - Certificado de Existencia y Representación: $6,800
   - Certificado de Matrícula Mercantil: $6,800
   - Entrega inmediata en línea

4. Consultas Empresariales
   - Asesoría para nuevos empresarios
   - Información sobre trámites

VALORES:
- Civismo
- Integridad
- Responsabilidad
- Lealtad
- Buen gobierno

MISIÓN: Transformar el tejido empresarial de Risaralda

Responde de forma amigable, profesional y concisa. 
Si no sabes algo, ofrece crear un ticket para que un funcionario te contacte.
Usa emojis ocasionalmente para ser más cercano.
"""

# =============================================================================
# BASE DE DATOS
# =============================================================================
def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    
    # Tabla de conversaciones
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de tickets
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT NOT NULL,
            telefono TEXT,
            asunto TEXT NOT NULL,
            descripcion TEXT NOT NULL,
            categoria TEXT DEFAULT 'general',
            prioridad TEXT DEFAULT 'normal',
            estado TEXT DEFAULT 'pendiente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de estadísticas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            valor TEXT NOT NULL,
            fecha DATE DEFAULT CURRENT_DATE
        )
    ''')
    
    conn.commit()
    conn.close()

# =============================================================================
# FUNCIONES DE IA
# =============================================================================
def analizar_intencion(mensaje):
    """Analiza la intención del mensaje para dar respuestas más precisas"""
    mensaje_lower = mensaje.lower()
    
    intenciones = {
        'certificado': ['certificado', 'certificación', 'documento', 'papel'],
        'renovacion': ['renovar', 'renovación', 'vencimiento', 'actualizar matrícula'],
        'crear_empresa': ['crear empresa', 'registrar empresa', 'nueva empresa', 'constituir'],
        'consulta_costo': ['cuánto cuesta', 'valor', 'precio', 'tarifa', 'cuánto vale'],
        'urgente': ['urgente', 'ya', 'ahora', 'inmediato', 'rápido', 'hoy']
    }
    
    detectadas = []
    for intencion, palabras_clave in intenciones.items():
        if any(palabra in mensaje_lower for palabra in palabras_clave):
            detectadas.append(intencion)
    
    return detectadas

def generar_sugerencias(mensaje):
    """Genera sugerencias proactivas basadas en el mensaje"""
    intenciones = analizar_intencion(mensaje)
    sugerencias = []
    
    if 'certificado' in intenciones:
        sugerencias.extend([
            "💡 ¿Sabías que puedes descargar certificados inmediatamente desde Servicios Virtuales?",
            "📱 Descarga la app móvil para obtener certificados desde tu celular"
        ])
    
    if 'renovacion' in intenciones:
        sugerencias.extend([
            "⏰ Recuerda: La fecha límite para renovar es el 31 de marzo",
            "💰 Renueva antes del vencimiento para evitar el 10% de sanción"
        ])
    
    if 'crear_empresa' in intenciones:
        sugerencias.extend([
            "🚀 Te recomiendo la SAS (Sociedad por Acciones Simplificada) si estás empezando",
            "📚 Tenemos talleres gratuitos de creación de empresas"
        ])
    
    return sugerencias

def llamar_ia(mensaje_usuario, historial=[]):
    """Llama a Groq API para obtener respuesta del chatbot con mejoras inteligentes"""
    
    if not GROQ_API_KEY:
        return {
            'respuesta': "⚠️ Lo siento, el servicio de IA no está configurado. ¿Quieres que cree un ticket para que te contactemos?",
            'sugerencias': [],
            'intenciones': []
        }
    
    try:
        # Analizar intenciones del usuario
        intenciones = analizar_intencion(mensaje_usuario)
        
        # Preparar mensajes para la IA con contexto mejorado
        system_prompt = CONOCIMIENTO_CCP + f"\n\nINTENCIONES DETECTADAS: {', '.join(intenciones) if intenciones else 'consulta general'}"
        
        mensajes = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Agregar historial si existe (últimos 3 intercambios)
        for msg in historial[-6:]:
            mensajes.append(msg)
        
        # Agregar mensaje actual
        mensajes.append({"role": "user", "content": mensaje_usuario})
        
        # Llamar a Groq API
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": mensajes,
                "temperature": 0.7,
                "max_tokens": 600  # Aumentado para respuestas más completas
            },
            timeout=30
        )
        
        if response.status_code == 200:
            respuesta = response.json()['choices'][0]['message']['content']
            sugerencias = generar_sugerencias(mensaje_usuario)
            
            return {
                'respuesta': respuesta,
                'sugerencias': sugerencias[:2],  # Máximo 2 sugerencias
                'intenciones': intenciones
            }
        else:
            return {
                'respuesta': "⚠️ Tuve un problema al procesar tu consulta. ¿Quieres crear un ticket?",
                'sugerencias': [],
                'intenciones': []
            }
            
    except Exception as e:
        print(f"Error en IA: {str(e)}")
        return {
            'respuesta': "⚠️ Ocurrió un error. ¿Quieres crear un ticket para que te contactemos?",
            'sugerencias': [],
            'intenciones': []
        }

def clasificar_categoria(texto):
    """Clasifica el texto en una categoría"""
    texto = texto.lower()
    
    if any(palabra in texto for palabra in ['renovar', 'renovación', 'matrícula', 'vencimiento']):
        return 'renovacion'
    elif any(palabra in texto for palabra in ['registrar', 'registro', 'nueva empresa', 'crear empresa']):
        return 'registro'
    elif any(palabra in texto for palabra in ['certificado', 'certificación', 'documento']):
        return 'certificados'
    elif any(palabra in texto for palabra in ['consulta', 'información', 'pregunta', 'duda']):
        return 'consulta'
    else:
        return 'general'

def clasificar_prioridad(texto):
    """Clasifica la prioridad basándose en palabras clave"""
    texto = texto.lower()
    
    urgentes = ['urgente', 'emergencia', 'ya', 'ahora', 'inmediato', 'hoy']
    if any(palabra in texto for palabra in urgentes):
        return 'urgente'
    
    altas = ['pronto', 'rápido', 'importante', 'necesito']
    if any(palabra in texto for palabra in altas):
        return 'alta'
    
    return 'normal'

# =============================================================================
# RUTAS DE LA APLICACIÓN
# =============================================================================

@app.route('/')
def index():
    """Página principal con el chatbot"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard para funcionarios"""
    conn = get_db()
    
    # Obtener estadísticas
    total_tickets = conn.execute('SELECT COUNT(*) as total FROM tickets').fetchone()['total']
    tickets_pendientes = conn.execute(
        "SELECT COUNT(*) as total FROM tickets WHERE estado = 'pendiente'"
    ).fetchone()['total']
    tickets_hoy = conn.execute(
        "SELECT COUNT(*) as total FROM tickets WHERE DATE(created_at) = DATE('now')"
    ).fetchone()['total']
    
    # Obtener últimos tickets
    tickets = conn.execute(
        'SELECT * FROM tickets ORDER BY created_at DESC LIMIT 10'
    ).fetchall()
    
    # Conversaciones recientes
    conversaciones = conn.execute(
        'SELECT COUNT(*) as total FROM conversations WHERE DATE(created_at) = DATE("now")'
    ).fetchone()['total']
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_tickets=total_tickets,
                         tickets_pendientes=tickets_pendientes,
                         tickets_hoy=tickets_hoy,
                         conversaciones=conversaciones,
                         tickets=tickets)

# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint principal del chatbot con capacidades mejoradas"""
    data = request.get_json()
    mensaje_usuario = data.get('message', '')
    historial = data.get('history', [])
    
    if not mensaje_usuario:
        return jsonify({'error': 'Mensaje vacío'}), 400
    
    # Obtener respuesta inteligente de la IA
    resultado_ia = llamar_ia(mensaje_usuario, historial)
    
    # Compatibilidad con versión anterior
    if isinstance(resultado_ia, str):
        respuesta_bot = resultado_ia
        sugerencias = []
        intenciones = []
    else:
        respuesta_bot = resultado_ia['respuesta']
        sugerencias = resultado_ia['sugerencias']
        intenciones = resultado_ia['intenciones']
    
    # Guardar en base de datos
    conn = get_db()
    conn.execute(
        'INSERT INTO conversations (user_message, bot_response) VALUES (?, ?)',
        (mensaje_usuario, respuesta_bot)
    )
    conn.commit()
    conn.close()
    
    # Detectar si el usuario necesita crear ticket
    necesita_ticket = any(palabra in respuesta_bot.lower() 
                         for palabra in ['ticket', 'contactemos', 'funcionario'])
    
    return jsonify({
        'response': respuesta_bot,
        'needs_ticket': necesita_ticket,
        'sugerencias': sugerencias,
        'intenciones': intenciones
    })

@app.route('/api/tickets', methods=['POST'])
def crear_ticket():
    """Crea un ticket de soporte"""
    data = request.get_json()
    
    nombre = data.get('nombre', '')
    email = data.get('email', '')
    telefono = data.get('telefono', '')
    asunto = data.get('asunto', '')
    descripcion = data.get('descripcion', '')
    
    if not all([nombre, email, asunto, descripcion]):
        return jsonify({'error': 'Faltan campos obligatorios'}), 400
    
    # Clasificar automáticamente
    categoria = clasificar_categoria(asunto + ' ' + descripcion)
    prioridad = clasificar_prioridad(asunto + ' ' + descripcion)
    
    # Guardar ticket
    conn = get_db()
    cursor = conn.execute(
        '''INSERT INTO tickets 
           (nombre, email, telefono, asunto, descripcion, categoria, prioridad) 
           VALUES (?, ?, ?, ?, ?, ?, ?)''',
        (nombre, email, telefono, asunto, descripcion, categoria, prioridad)
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'categoria': categoria,
        'prioridad': prioridad,
        'message': f'Ticket #{ticket_id} creado exitosamente. Te contactaremos pronto.'
    })

@app.route('/api/tickets', methods=['GET'])
def listar_tickets():
    """Lista todos los tickets"""
    conn = get_db()
    tickets = conn.execute(
        'SELECT * FROM tickets ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    
    return jsonify([dict(ticket) for ticket in tickets])

@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def actualizar_ticket(ticket_id):
    """Actualiza el estado de un ticket"""
    data = request.get_json()
    estado = data.get('estado', 'pendiente')
    
    conn = get_db()
    conn.execute(
        'UPDATE tickets SET estado = ? WHERE id = ?',
        (estado, ticket_id)
    )
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Ticket actualizado'})

@app.route('/api/stats', methods=['GET'])
def obtener_estadisticas():
    """Obtiene estadísticas del sistema"""
    conn = get_db()
    
    # Tickets por categoría
    por_categoria = conn.execute('''
        SELECT categoria, COUNT(*) as total 
        FROM tickets 
        GROUP BY categoria
    ''').fetchall()
    
    # Tickets por prioridad
    por_prioridad = conn.execute('''
        SELECT prioridad, COUNT(*) as total 
        FROM tickets 
        GROUP BY prioridad
    ''').fetchall()
    
    # Conversaciones por día (últimos 7 días)
    conversaciones_diarias = conn.execute('''
        SELECT DATE(created_at) as fecha, COUNT(*) as total
        FROM conversations
        WHERE created_at >= DATE('now', '-7 days')
        GROUP BY DATE(created_at)
    ''').fetchall()
    
    conn.close()
    
    return jsonify({
        'por_categoria': [dict(row) for row in por_categoria],
        'por_prioridad': [dict(row) for row in por_prioridad],
        'conversaciones_diarias': [dict(row) for row in conversaciones_diarias]
    })

@app.route('/api/health', methods=['GET'])
def health():
    """Verifica que el servicio esté funcionando"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'ia_configurada': bool(GROQ_API_KEY)
    })

# =============================================================================
# INICIALIZACIÓN
# =============================================================================

if __name__ == '__main__':
    # Crear base de datos si no existe
    init_db()
    print("✅ Base de datos inicializada")
    print("🚀 Servidor iniciando en http://localhost:5000")
    print("📊 Dashboard disponible en http://localhost:5000/dashboard")
    
    if not GROQ_API_KEY:
        print("⚠️  ADVERTENCIA: GROQ_API_KEY no configurada")
        print("   El chatbot funcionará en modo limitado")
    
    app.run(debug=True, host='0.0.0.0', port=5000)