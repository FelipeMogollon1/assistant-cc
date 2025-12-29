"""
ASISTENTE VIRTUAL - CAMARA DE COMERCIO DE PEREIRA
Sistema de chatbot inteligente con IA para atencion al cliente 24/7
Desarrollado con Flask + Groq API (LLaMA 3.3)
"""

from flask import Flask, render_template, request, jsonify
from datetime import datetime
import sqlite3
import os
import requests
import json
from dotenv import load_dotenv

# Cargar variables de entorno (.env)
load_dotenv()

# Inicializar aplicacion Flask
app = Flask(__name__)

# =============================================================================
# CONFIGURACION UTF-8
# =============================================================================
# Importante: Asegurar que todas las respuestas JSON manejen correctamente
# caracteres especiales en espanol (tildes, enies, etc.)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# =============================================================================
# CONFIGURACION DE IA (Groq API)
# =============================================================================
# Groq ofrece API gratuita para modelos de lenguaje (LLaMA, Mixtral, etc.)
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# =============================================================================
# BASE DE CONOCIMIENTO
# =============================================================================
# Este es el "cerebro" del chatbot. Contiene toda la informacion institucional
# que el modelo de IA usara para responder preguntas de los usuarios.
# Nota: Sin tildes para evitar problemas de codificacion con algunos sistemas.

CONOCIMIENTO_CCP = """
Eres un asistente virtual de la Camara de Comercio de Pereira por Risaralda.
Web oficial: https://www.camarapereira.org.co/es/

=== INFORMACION INSTITUCIONAL ===
- Fundada en 1926
- Entidad privada sin animo de lucro
- Presta servicios de Registros Publicos
- Jurisdiccion: Pereira, Apia, Balboa, Belen de Umbria, Guatica, La Celia, 
  La Virginia, Marsella, Mistrato, Pueblo Rico, Quinchia y Santuario (Risaralda)

VALORES: Civismo, Integridad, Responsabilidad, Lealtad, Buen gobierno
MISION: Transformar el tejido empresarial de Risaralda

=== SEDES Y HORARIOS ===

SEDE PRINCIPAL PEREIRA - Sede Administrativa
Direccion: Carrera 8a No. 23-09 Local 10
Telefono: (606) 340 3030
Email: servicioalcliente@camarapereira.org.co
Horario: Lunes a viernes 8:00 a.m. a 4:00 p.m. (Jornada continua)

SEDE VILLA OLIMPICA (Anterior Sede Cuba)
Direccion: Carrera 19 No. 93-02 Villa Olimpica
Telefono: (606) 340 3030 ext. 6000
WhatsApp: 320 350 9700
Email: servicioalcliente@camarapereira.org.co
Horario: Lunes a viernes 8:00 a.m. a 4:00 p.m. (Jornada continua)

=== SEDES EN MUNICIPIOS ===
Todas con horario: Lunes a viernes 8:00 am a 12:00 m - 1:00 pm a 4:30 pm

LA VIRGINIA
Direccion: Carrera 7A No. 6-60
WhatsApp: 310 315 7066
Extension: 9000

BELEN DE UMBRIA
Direccion: Calle 4 No. 10-36
WhatsApp: 310 315 7133
Extension: 9001

MARSELLA
Direccion: Carrera 9 No. 7-23 Plaza Principal
WhatsApp: 310 315 7337
Extension: 9002

QUINCHIA
Direccion: Carrera 7 No. 4-43 Local 2
WhatsApp: 310 315 7299
Extension: 9005

SANTUARIO
Direccion: Calle 5ta No. 5-46 (Cerca plaza principal)
WhatsApp: 310 315 7144
Extension: 9004

APIA
Direccion: Calle 11 No. 7-44 Local 2
WhatsApp: 310 315 7188
Extension: 9003

=== OTROS SERVICIOS ===

CENTRO DE ARBITRAJE Y CONCILIACION
Direccion: Carrera 8a No. 23-09
Telefono: (606) 340 3030
Email: cac@camarapereira.org.co
Horario: Lunes a Viernes 8:00 a.m. a 12:00 m y 2:00 p.m. a 5:00 p.m.

EXPOFUTURO - Centro de Convenciones
Direccion: Carrera 19 No. 93-02 Villa Olimpica
Telefono: (606) 340 1500
Email: info@expofuturo.com
Horario: Lunes a Viernes 8:00 a.m. a 12:30 m y 1:30 p.m. a 5:00 p.m.

=== SERVICIOS PRINCIPALES ===

1. RENOVACION DE MATRICULA MERCANTIL
   - Fecha limite: 31 de marzo de cada ano
   - Disponible en linea o presencial
   - Costo segun activos de la empresa
   - IMPORTANTE: Sabados NO son dias habiles para conteo de terminos

2. REGISTRO DE EMPRESAS
   - Persona Natural o Juridica
   - Requisitos: RUT, Formulario de registro, Documento de identidad
   - Solicitudes electronicas en horario no habil se cuentan desde el dia habil siguiente

3. CERTIFICADOS
   - Certificado de Existencia y Representacion: $6,800
   - Certificado de Matricula Mercantil: $6,800
   - Entrega inmediata en linea

4. CONSULTAS Y ASESORIAS
   - Asesoria para nuevos empresarios
   - Informacion sobre tramites
   - Talleres de formacion empresarial

=== INFORMACION IMPORTANTE ===
- El SABADO NO es dia habil para conteo de terminos de registro
- Solicitudes por medios electronicos en dias/horas no habiles: 
  terminos se cuentan desde el dia habil siguiente
- Circular Externa No. 100-000002 de 2022 - Superintendencia de Sociedades

=== INSTRUCCIONES DE RESPUESTA ===
- Responde de forma amigable, profesional y concisa
- Si preguntan por ubicacion, siempre incluye direccion, telefono y horario
- Si preguntan por horarios, menciona que Pereira tiene jornada continua
- Para municipios, aclara el horario partido (manana y tarde)
- Sugiere la sede mas cercana segun la ubicacion del usuario
- Si no sabes algo especifico, ofrece crear un ticket
- Puedes usar emojis ocasionalmente para ser mas cercano
- Siempre proporciona informacion de contacto relevante (telefono, WhatsApp, email)
"""

# =============================================================================
# FUNCIONES DE BASE DE DATOS
# =============================================================================

def get_db():
    """
    Crea y retorna una conexion a la base de datos SQLite.
    Configurada para usar UTF-8 y retornar resultados como diccionarios.
    """
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    conn.execute('PRAGMA encoding = "UTF-8"')  # Forzar UTF-8
    return conn


def init_db():
    """
    Inicializa la base de datos creando las tablas necesarias si no existen.
    Se ejecuta automaticamente al iniciar la aplicacion.
    """
    conn = get_db()
    
    # Tabla de conversaciones: Almacena historico de interacciones
    conn.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            bot_response TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de tickets: Sistema de soporte para casos que requieren atencion humana
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
    
    # Tabla de estadisticas: Para analisis y metricas
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
    print("Base de datos inicializada correctamente")


# =============================================================================
# SISTEMA DE ANALISIS DE INTENCIONES
# =============================================================================

def analizar_intencion(mensaje):
    """
    Analiza el mensaje del usuario para detectar que tipo de informacion busca.
    Esto permite dar respuestas mas precisas y contextuales.
    
    Args:
        mensaje (str): Mensaje del usuario
    
    Returns:
        list: Lista de intenciones detectadas
    
    Ejemplo:
        analizar_intencion("Donde estan ubicados?")
        -> ['ubicacion']
    """
    mensaje_lower = mensaje.lower()
    
    # Diccionario de intenciones con palabras clave asociadas
    intenciones = {
        'certificado': ['certificado', 'certificacion', 'documento', 'papel'],
        'renovacion': ['renovar', 'renovacion', 'vencimiento', 'actualizar', 'matricula'],
        'crear_empresa': ['crear empresa', 'registrar', 'nueva empresa', 'constituir'],
        'consulta_costo': ['cuanto cuesta', 'valor', 'precio', 'tarifa', 'cuanto vale'],
        'ubicacion': ['donde', 'ubicacion', 'direccion', 'sede', 'oficina', 'quedan', 'ubicados'],
        'horario': ['horario', 'hora', 'cuando abren', 'cuando cierran', 'atencion', 'abierto'],
        'contacto': ['telefono', 'whatsapp', 'email', 'correo', 'contacto', 'llamar'],
        'municipio': ['virginia', 'belen', 'marsella', 'quinchia', 'santuario', 'apia'],
        'urgente': ['urgente', 'ya', 'ahora', 'inmediato', 'rapido', 'hoy']
    }
    
    # Detectar todas las intenciones presentes en el mensaje
    detectadas = []
    for intencion, palabras_clave in intenciones.items():
        if any(palabra in mensaje_lower for palabra in palabras_clave):
            detectadas.append(intencion)
    
    return detectadas


def generar_sugerencias(mensaje):
    """
    Genera sugerencias proactivas basadas en las intenciones detectadas.
    Ayuda a guiar al usuario hacia informacion relevante adicional.
    
    Args:
        mensaje (str): Mensaje del usuario
    
    Returns:
        list: Lista de hasta 2 sugerencias relevantes
    """
    intenciones = analizar_intencion(mensaje)
    sugerencias = []
    
    # Generar sugerencias contextuales
    if 'certificado' in intenciones:
        sugerencias.append("Puedes descargar certificados inmediatamente en linea por $6,800")
    
    if 'renovacion' in intenciones:
        sugerencias.append("Fecha limite: 31 de marzo. Sabados NO son dias habiles")
    
    if 'crear_empresa' in intenciones:
        sugerencias.append("La SAS es ideal si estas empezando")
    
    if 'ubicacion' in intenciones:
        sugerencias.append("Tenemos 2 sedes en Pereira y 6 en municipios de Risaralda")
    
    if 'horario' in intenciones:
        sugerencias.append("Pereira: 8am-4pm continuo. Municipios: 8am-12m y 1pm-4:30pm")
    
    if 'contacto' in intenciones:
        sugerencias.append("Linea principal: (606) 340 3030")
    
    # Retornar maximo 2 sugerencias
    return sugerencias[:2]


# =============================================================================
# SISTEMA DE INTELIGENCIA ARTIFICIAL
# =============================================================================

def llamar_ia(mensaje_usuario, historial=[]):
    """
    Funcion principal que interactua con la API de Groq (LLaMA 3.3).
    Envia el mensaje del usuario junto con el contexto de la Camara de Comercio
    y retorna una respuesta inteligente.
    
    Args:
        mensaje_usuario (str): Pregunta o mensaje del usuario
        historial (list): Historial de conversacion (ultimos 6 mensajes)
    
    Returns:
        dict: {
            'respuesta': str,      # Respuesta generada por la IA
            'sugerencias': list,   # Sugerencias proactivas
            'intenciones': list    # Intenciones detectadas
        }
    """
    
    # Verificar que la API key este configurada
    if not GROQ_API_KEY:
        return {
            'respuesta': "Lo siento, el servicio de IA no esta configurado. Quieres crear un ticket?",
            'sugerencias': [],
            'intenciones': []
        }
    
    try:
        # Analizar intenciones del usuario
        intenciones = analizar_intencion(mensaje_usuario)
        
        # Construir el prompt del sistema con contexto
        system_prompt = CONOCIMIENTO_CCP + f"\n\nINTENCIONES DETECTADAS: {', '.join(intenciones) if intenciones else 'consulta general'}"
        
        # Preparar mensajes para la API
        mensajes = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Agregar historial de conversacion (ultimos 3 intercambios = 6 mensajes)
        for msg in historial[-6:]:
            mensajes.append(msg)
        
        # Agregar mensaje actual del usuario
        mensajes.append({"role": "user", "content": mensaje_usuario})
        
        # Llamar a Groq API
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Modelo LLaMA 3.3 (70B parametros)
                "messages": mensajes,
                "temperature": 0.7,  # Controla creatividad (0.0 = conservador, 1.0 = creativo)
                "max_tokens": 600     # Longitud maxima de respuesta
            },
            timeout=30  # Timeout de 30 segundos
        )
        
        # Procesar respuesta exitosa
        if response.status_code == 200:
            respuesta_texto = response.json()['choices'][0]['message']['content']
            sugerencias = generar_sugerencias(mensaje_usuario)
            
            return {
                'respuesta': respuesta_texto,
                'sugerencias': sugerencias,
                'intenciones': intenciones
            }
        else:
            # Error en la API
            return {
                'respuesta': "Tuve un problema al procesar tu consulta. Quieres crear un ticket?",
                'sugerencias': [],
                'intenciones': []
            }
            
    except Exception as e:
        # Manejo de errores generales
        print(f"Error en llamada a IA: {str(e)}")
        return {
            'respuesta': "Ocurrio un error inesperado. Quieres crear un ticket para que te contactemos?",
            'sugerencias': [],
            'intenciones': []
        }


# =============================================================================
# SISTEMA DE CLASIFICACION AUTOMATICA
# =============================================================================

def clasificar_categoria(texto):
    """
    Clasifica automaticamente un texto en una categoria.
    Usado para organizar tickets por tipo de consulta.
    
    Args:
        texto (str): Texto a clasificar (asunto + descripcion)
    
    Returns:
        str: Categoria ('renovacion', 'registro', 'certificados', 'consulta', 'general')
    """
    texto = texto.lower()
    
    if any(p in texto for p in ['renovar', 'renovacion', 'matricula', 'vencimiento']):
        return 'renovacion'
    elif any(p in texto for p in ['registrar', 'registro', 'nueva empresa', 'crear']):
        return 'registro'
    elif any(p in texto for p in ['certificado', 'certificacion', 'documento']):
        return 'certificados'
    elif any(p in texto for p in ['consulta', 'informacion', 'pregunta', 'duda']):
        return 'consulta'
    else:
        return 'general'


def clasificar_prioridad(texto):
    """
    Clasifica automaticamente la prioridad de un ticket.
    Ayuda a los funcionarios a atender casos urgentes primero.
    
    Args:
        texto (str): Texto a analizar (asunto + descripcion)
    
    Returns:
        str: Prioridad ('urgente', 'alta', 'normal')
    """
    texto = texto.lower()
    
    # Palabras clave de urgencia
    if any(p in texto for p in ['urgente', 'emergencia', 'ya', 'ahora', 'inmediato', 'hoy']):
        return 'urgente'
    
    # Palabras clave de prioridad alta
    if any(p in texto for p in ['pronto', 'rapido', 'importante', 'necesito']):
        return 'alta'
    
    # Por defecto: prioridad normal
    return 'normal'


# =============================================================================
# RUTAS WEB - PAGINAS
# =============================================================================

@app.route('/')
def index():
    """
    Pagina principal: Interfaz del chatbot para usuarios.
    Renderiza el template index.html con el chat interactivo.
    """
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    """
    Dashboard administrativo: Panel para funcionarios de la Camara de Comercio.
    Muestra estadisticas, tickets pendientes y metricas de uso del chatbot.
    """
    conn = get_db()
    
    # Obtener metricas generales
    total_tickets = conn.execute('SELECT COUNT(*) as total FROM tickets').fetchone()['total']
    tickets_pendientes = conn.execute(
        "SELECT COUNT(*) as total FROM tickets WHERE estado = 'pendiente'"
    ).fetchone()['total']
    tickets_hoy = conn.execute(
        "SELECT COUNT(*) as total FROM tickets WHERE DATE(created_at) = DATE('now')"
    ).fetchone()['total']
    
    # Obtener ultimos tickets
    tickets = conn.execute(
        'SELECT * FROM tickets ORDER BY created_at DESC LIMIT 10'
    ).fetchall()
    
    # Conversaciones del dia
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
# API ENDPOINTS - CHATBOT
# =============================================================================

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint principal del chatbot.
    Recibe un mensaje del usuario y retorna una respuesta generada por IA.
    
    Request JSON:
        {
            "message": "Donde estan ubicados?",
            "history": [...]  # Opcional: historial de conversacion
        }
    
    Response JSON:
        {
            "response": "Nuestra sede principal...",
            "needs_ticket": false,
            "sugerencias": ["..."],
            "intenciones": ["ubicacion"]
        }
    """
    try:
        # Obtener datos del request
        data = request.get_json(force=True)
        mensaje_usuario = data.get('message', '').strip()
        historial = data.get('history', [])
        
        # Validar que el mensaje no este vacio
        if not mensaje_usuario:
            return jsonify({'error': 'Mensaje vacio'}), 400
        
        # Obtener respuesta de la IA
        resultado_ia = llamar_ia(mensaje_usuario, historial)
        
        # Compatibilidad con versiones anteriores
        if isinstance(resultado_ia, str):
            respuesta_bot = resultado_ia
            sugerencias = []
            intenciones = []
        else:
            respuesta_bot = resultado_ia['respuesta']
            sugerencias = resultado_ia['sugerencias']
            intenciones = resultado_ia['intenciones']
        
        # Guardar conversacion en la base de datos
        conn = get_db()
        conn.execute(
            'INSERT INTO conversations (user_message, bot_response) VALUES (?, ?)',
            (mensaje_usuario, respuesta_bot)
        )
        conn.commit()
        conn.close()
        
        # Detectar si el bot sugiere crear un ticket
        necesita_ticket = any(p in respuesta_bot.lower() 
                             for p in ['ticket', 'contactemos', 'funcionario'])
        
        # Retornar respuesta con encoding UTF-8
        return jsonify({
            'response': respuesta_bot,
            'needs_ticket': necesita_ticket,
            'sugerencias': sugerencias,
            'intenciones': intenciones
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}
        
    except Exception as e:
        print(f"Error en /api/chat: {str(e)}")
        return jsonify({
            'error': 'Error al procesar mensaje',
            'details': str(e)
        }), 500


# =============================================================================
# API ENDPOINTS - SISTEMA DE TICKETS
# =============================================================================

@app.route('/api/tickets', methods=['POST'])
def crear_ticket():
    """
    Crea un nuevo ticket de soporte.
    Los tickets son atendidos por funcionarios de la Camara de Comercio.
    
    Request JSON:
        {
            "nombre": "Juan Perez",
            "email": "juan@example.com",
            "telefono": "3001234567",
            "asunto": "Consulta sobre renovacion",
            "descripcion": "Necesito informacion..."
        }
    
    Response JSON:
        {
            "success": true,
            "ticket_id": 123,
            "categoria": "renovacion",
            "prioridad": "normal",
            "message": "Ticket #123 creado exitosamente..."
        }
    """
    try:
        data = request.get_json(force=True)
        
        # Extraer y validar campos
        nombre = data.get('nombre', '').strip()
        email = data.get('email', '').strip()
        telefono = data.get('telefono', '').strip()
        asunto = data.get('asunto', '').strip()
        descripcion = data.get('descripcion', '').strip()
        
        # Validar campos obligatorios
        if not all([nombre, email, asunto, descripcion]):
            return jsonify({'error': 'Faltan campos obligatorios'}), 400
        
        # Clasificar automaticamente
        categoria = clasificar_categoria(asunto + ' ' + descripcion)
        prioridad = clasificar_prioridad(asunto + ' ' + descripcion)
        
        # Guardar ticket en la base de datos
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
        }), 200, {'Content-Type': 'application/json; charset=utf-8'}
        
    except Exception as e:
        print(f"Error en /api/tickets POST: {str(e)}")
        return jsonify({'error': 'Error al crear ticket'}), 500


@app.route('/api/tickets', methods=['GET'])
def listar_tickets():
    """
    Lista todos los tickets creados (mas recientes primero).
    Usado por el dashboard administrativo.
    """
    conn = get_db()
    tickets = conn.execute(
        'SELECT * FROM tickets ORDER BY created_at DESC'
    ).fetchall()
    conn.close()
    
    return jsonify([dict(ticket) for ticket in tickets])


@app.route('/api/tickets/<int:ticket_id>', methods=['PUT'])
def actualizar_ticket(ticket_id):
    """
    Actualiza el estado de un ticket.
    Estados posibles: 'pendiente', 'en_proceso', 'resuelto', 'cerrado'
    
    Request JSON:
        {
            "estado": "resuelto"
        }
    """
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


# =============================================================================
# API ENDPOINTS - ESTADISTICAS
# =============================================================================

@app.route('/api/stats', methods=['GET'])
def obtener_estadisticas():
    """
    Obtiene estadisticas del sistema para el dashboard.
    Incluye metricas por categoria, prioridad y actividad diaria.
    """
    conn = get_db()
    
    # Tickets por categoria
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
    
    # Conversaciones por dia (ultimos 7 dias)
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
    """
    Endpoint de salud: Verifica que el servicio este funcionando.
    Util para monitoreo y debugging.
    """
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'ia_configurada': bool(GROQ_API_KEY)
    })


# =============================================================================
# MANEJO DE ERRORES
# =============================================================================

@app.errorhandler(500)
def error_interno(e):
    """Maneja errores internos del servidor (500)"""
    return jsonify({'error': 'Error interno del servidor'}), 500


@app.errorhandler(404)
def no_encontrado(e):
    """Maneja rutas no encontradas (404)"""
    return jsonify({'error': 'Recurso no encontrado'}), 404


# =============================================================================
# INICIALIZACION Y EJECUCION
# =============================================================================

if __name__ == '__main__':
    # Inicializar base de datos
    init_db()
    
    # Mensajes informativos
    print("\n" + "="*60)
    print("ASISTENTE VIRTUAL - CAMARA DE COMERCIO DE PEREIRA")
    print("="*60)
    print(f"Servidor iniciando en: http://localhost:5000")
    print(f"Dashboard disponible en: http://localhost:5000/dashboard")
    print(f"Estado IA: {'Configurada' if GROQ_API_KEY else 'NO CONFIGURADA'}")
    
    if not GROQ_API_KEY:
        print("\nADVERTENCIA: Variable GROQ_API_KEY no encontrada en .env")
        print("El chatbot funcionara en modo limitado sin IA")
    
    print("="*60 + "\n")
    
    # Iniciar servidor Flask
    app.run(debug=True, host='0.0.0.0', port=5000)