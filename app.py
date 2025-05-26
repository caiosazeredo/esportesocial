from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import requests
import json
import os
from functools import wraps
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# APIs Configuration - Usando variáveis de ambiente
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
API_FUTEBOL_KEY = os.environ.get('API_FUTEBOL_KEY')

# Brazilian Serie A Championship ID
BRASILEIRAO_ID = 10  # ID do Campeonato Brasileiro na API-Futebol.com.br

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)
    favorite_team = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    establishment_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_match_id = db.Column(db.Integer, unique=True)
    home_team = db.Column(db.String(50), nullable=False)
    away_team = db.Column(db.String(50), nullable=False)
    match_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='scheduled')
    home_score = db.Column(db.Integer, default=0)
    away_score = db.Column(db.Integer, default=0)
    round_number = db.Column(db.Integer)

class UserMatchInterest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), nullable=False)
    supporting_team = db.Column(db.String(50), nullable=False)
    ranking = db.Column(db.Integer, default=1)
    establishment_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    room_id = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='messages')

# Brazilian teams colors
TEAM_COLORS = {
    'Flamengo': {'primary': '#E60026', 'secondary': '#000000'},
    'Corinthians': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Palmeiras': {'primary': '#006B3F', 'secondary': '#FFFFFF'},
    'São Paulo': {'primary': '#FF0000', 'secondary': '#000000'},
    'Santos': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Vasco': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Botafogo': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Fluminense': {'primary': '#7F0000', 'secondary': '#FFFFFF'},
    'Grêmio': {'primary': '#0080FF', 'secondary': '#000000'},
    'Internacional': {'primary': '#FF0000', 'secondary': '#FFFFFF'},
    'Atlético-MG': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Cruzeiro': {'primary': '#0080FF', 'secondary': '#FFFFFF'},
    'Bahia': {'primary': '#0080FF', 'secondary': '#FF0000'},
    'Sport': {'primary': '#FF0000', 'secondary': '#000000'},
    'Ceará': {'primary': '#000000', 'secondary': '#FFFFFF'},
    'Fortaleza': {'primary': '#FF0000', 'secondary': '#0080FF'},
    'Athletico-PR': {'primary': '#FF0000', 'secondary': '#000000'},
    'Coritiba': {'primary': '#00FF00', 'secondary': '#FFFFFF'},
    'Bragantino': {'primary': '#FF0000', 'secondary': '#FFFFFF'},
    'Cuiabá': {'primary': '#FFD700', 'secondary': '#00FF00'},
    'Atlético-GO': {'primary': '#FF0000', 'secondary': '#000000'},
    'Vitória': {'primary': '#FF0000', 'secondary': '#000000'},
    'Criciúma': {'primary': '#FFD700', 'secondary': '#000000'},
    'Juventude': {'primary': '#00FF00', 'secondary': '#FFFFFF'}
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def validate_api_keys():
    """Valida se as chaves de API estão configuradas"""
    missing_keys = []
    
    if not GOOGLE_MAPS_API_KEY:
        missing_keys.append('GOOGLE_MAPS_API_KEY')
    
    if not API_FUTEBOL_KEY:
        missing_keys.append('API_FUTEBOL_KEY')
    
    if missing_keys:
        print(f"⚠️  ATENÇÃO: Configure as seguintes chaves no arquivo .env: {', '.join(missing_keys)}")
        return False
    
    print("✅ Chaves de API configuradas")
    return True

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email já cadastrado'})
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            user_type=data['user_type'],
            favorite_team=data.get('favorite_team'),
            establishment_name=data.get('establishment_name')
        )
        
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        return jsonify({'success': True})
    
    return render_template('register.html', teams=list(TEAM_COLORS.keys()))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password_hash, data['password']):
            session['user_id'] = user.id
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'message': 'Credenciais inválidas'})
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = User.query.get(session['user_id'])
    team_colors = TEAM_COLORS.get(user.favorite_team, {'primary': '#007BFF', 'secondary': '#FFFFFF'})
    return render_template('dashboard.html', user=user, team_colors=team_colors)

@app.route('/location', methods=['POST'])
@login_required
def update_location():
    data = request.get_json()
    user = User.query.get(session['user_id'])
    user.latitude = data['latitude']
    user.longitude = data['longitude']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/nearby-establishments')
@login_required
def nearby_establishments():
    user = User.query.get(session['user_id'])
    if not user.latitude or not user.longitude:
        return jsonify({'establishments': []})
    
    # Verificar se Google Maps API está configurada
    if not GOOGLE_MAPS_API_KEY:
        return jsonify({'establishments': [], 'error': 'Google Maps API não configurada'})
    
    # Google Places API call
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        'location': f"{user.latitude},{user.longitude}",
        'radius': 2000,
        'type': 'bar',
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(places_url, params=params, timeout=10)
        places_data = response.json()
        
        if places_data.get('status') != 'OK':
            return jsonify({'establishments': [], 'error': f"Google API Error: {places_data.get('status')}"})
        
        establishments = []
        for place in places_data.get('results', []):
            establishments.append({
                'name': place['name'],
                'address': place.get('vicinity', ''),
                'rating': place.get('rating', 0),
                'place_id': place['place_id']
            })
        
        return jsonify({'establishments': establishments})
    except requests.exceptions.RequestException as e:
        return jsonify({'establishments': [], 'error': f'Erro de rede: {str(e)}'})
    except Exception as e:
        return jsonify({'establishments': [], 'error': f'Erro: {str(e)}'})

@app.route('/matches/today')
@login_required
def matches_today():
    today = datetime.now()
    
    # Verificar se API de futebol está configurada
    if not API_FUTEBOL_KEY:
        return jsonify({'matches': [], 'error': 'API de futebol não configurada'})
    
    # API-Futebol.com.br call
    headers = {
        'Authorization': f'Bearer {API_FUTEBOL_KEY}'
    }
    
    try:
        # Get current championship edition
        championship_url = f"https://api.api-futebol.com.br/v1/campeonatos/{BRASILEIRAO_ID}"
        championship_response = requests.get(championship_url, headers=headers, timeout=10)
        championship_data = championship_response.json()
        
        if 'edicao_atual' in championship_data:
            edition_id = championship_data['edicao_atual']['edicao_id']
            
            # Get matches for today
            matches_url = f"https://api.api-futebol.com.br/v1/campeonatos/{BRASILEIRAO_ID}/fases/{edition_id}/jogos"
            params = {
                'data': today.strftime('%Y-%m-%d')
            }
            
            matches_response = requests.get(matches_url, headers=headers, params=params, timeout=10)
            matches_data = matches_response.json()
            
            matches = []
            for match in matches_data:
                match_datetime = datetime.strptime(match['data_realizacao'], '%Y-%m-%d %H:%M:%S')
                
                match_data = {
                    'id': match['jogo_id'],
                    'home_team': match['time_mandante']['nome_popular'],
                    'away_team': match['time_visitante']['nome_popular'],
                    'date': match_datetime.isoformat(),
                    'status': match['status'],
                    'home_score': match.get('placar_mandante', 0),
                    'away_score': match.get('placar_visitante', 0),
                    'round': match.get('rodada', 1)
                }
                matches.append(match_data)
                
                # Save to database
                existing_match = Match.query.filter_by(api_match_id=match['jogo_id']).first()
                if not existing_match:
                    new_match = Match(
                        api_match_id=match['jogo_id'],
                        home_team=match['time_mandante']['nome_popular'],
                        away_team=match['time_visitante']['nome_popular'],
                        match_date=match_datetime,
                        status=match['status'],
                        home_score=match.get('placar_mandante', 0),
                        away_score=match.get('placar_visitante', 0),
                        round_number=match.get('rodada', 1)
                    )
                    db.session.add(new_match)
                else:
                    # Update existing match
                    existing_match.status = match['status']
                    existing_match.home_score = match.get('placar_mandante', 0)
                    existing_match.away_score = match.get('placar_visitante', 0)
            
            db.session.commit()
            return jsonify({'matches': matches})
        
        return jsonify({'matches': [], 'error': 'Campeonato não encontrado'})
        
    except requests.exceptions.RequestException as e:
        return jsonify({'matches': [], 'error': f'Erro de rede: {str(e)}'})
    except Exception as e:
        print(f"Error fetching matches: {e}")
        return jsonify({'matches': [], 'error': f'Erro: {str(e)}'})

@app.route('/match/interest', methods=['POST'])
@login_required
def add_match_interest():
    data = request.get_json()
    
    # Remove existing interest for this match
    existing = UserMatchInterest.query.filter_by(
        user_id=session['user_id'],
        match_id=data['match_id']
    ).first()
    
    if existing:
        db.session.delete(existing)
    
    # Add new interest
    interest = UserMatchInterest(
        user_id=session['user_id'],
        match_id=data['match_id'],
        supporting_team=data['supporting_team'],
        ranking=data['ranking']
    )
    
    db.session.add(interest)
    db.session.commit()
    
    return jsonify({'success': True})

@app.route('/chat/<room_id>')
@login_required
def chat_room(room_id):
    user = User.query.get(session['user_id'])
    team_colors = TEAM_COLORS.get(user.favorite_team, {'primary': '#007BFF', 'secondary': '#FFFFFF'})
    
    # Get chat history
    messages = ChatMessage.query.filter_by(room_id=room_id)\
        .order_by(ChatMessage.timestamp.desc())\
        .limit(50).all()
    
    return render_template('chat.html', 
                         room_id=room_id, 
                         user=user, 
                         messages=reversed(messages),
                         team_colors=team_colors)

# WebSocket events
@socketio.on('join')
def on_join(data):
    if 'user_id' not in session:
        return
    
    room = data['room']
    join_room(room)
    user = User.query.get(session['user_id'])
    emit('status', {'msg': f'{user.username} entrou no chat'}, room=room)

@socketio.on('leave')
def on_leave(data):
    if 'user_id' not in session:
        return
        
    room = data['room']
    leave_room(room)
    user = User.query.get(session['user_id'])
    emit('status', {'msg': f'{user.username} saiu do chat'}, room=room)

@socketio.on('message')
def handle_message(data):
    if 'user_id' not in session:
        return
        
    room = data['room']
    message_text = data['message']
    message_type = data.get('type', 'text')
    
    # Save message to database
    message = ChatMessage(
        user_id=session['user_id'],
        room_id=room,
        message=message_text,
        message_type=message_type
    )
    db.session.add(message)
    db.session.commit()
    
    user = User.query.get(session['user_id'])
    team_colors = TEAM_COLORS.get(user.favorite_team, {'primary': '#007BFF', 'secondary': '#FFFFFF'})
    
    emit('message', {
        'username': user.username,
        'message': message_text,
        'type': message_type,
        'timestamp': message.timestamp.strftime('%H:%M'),
        'team_colors': team_colors
    }, room=room)

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message='Página não encontrada'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error.html', 
                         error_code=500, 
                         error_message='Erro interno do servidor'), 500

# Create tables
def create_tables():
    with app.app_context():
        try:
            db.create_all()
            print("✅ Tabelas do banco criadas com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {e}")

if __name__ == '__main__':
    # Validar configuração
    validate_api_keys()
    
    # Criar tabelas
    create_tables()
    
    # Executar aplicação
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Iniciando EsporteSocial na porta {port}")
    print(f"🌐 Acesse: http://localhost:{port}")
    
    socketio.run(app, 
                debug=debug, 
                host='0.0.0.0', 
                port=port,
                allow_unsafe_werkzeug=True)