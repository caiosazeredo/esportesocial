import requests
import json
from datetime import datetime, timedelta
from functools import wraps
from flask import session, jsonify, current_app
import time

def validate_api_keys():
    """Valida se as chaves de API estão configuradas"""
    google_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
    football_key = current_app.config.get('FOOTBALL_API_KEY') or current_app.config.get('API_FUTEBOL_KEY')
    
    missing_keys = []
    
    if not google_key:
        missing_keys.append('GOOGLE_MAPS_API_KEY')
    
    if not football_key:
        missing_keys.append('FOOTBALL_API_KEY or API_FUTEBOL_KEY')
    
    if missing_keys:
        print(f"⚠️  ATENÇÃO: As seguintes chaves de API não estão configuradas: {', '.join(missing_keys)}")
        print("📋 Configure as chaves no arquivo .env ou como variáveis de ambiente")
        return False
    
    print("✅ Todas as chaves de API estão configuradas")
    return True

def cache_response(timeout=300):
    """Decorator para cache simples de respostas"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"
            
            # Implementação simples de cache em memória
            if not hasattr(decorated_function, '_cache'):
                decorated_function._cache = {}
            
            now = time.time()
            
            # Verifica se existe cache válido
            if cache_key in decorated_function._cache:
                data, timestamp = decorated_function._cache[cache_key]
                if now - timestamp < timeout:
                    return data
            
            # Executa função e armazena no cache
            result = f(*args, **kwargs)
            decorated_function._cache[cache_key] = (result, now)
            
            # Limpa cache antigo (mantém apenas últimas 100 entradas)
            if len(decorated_function._cache) > 100:
                old_keys = list(decorated_function._cache.keys())[:-50]
                for key in old_keys:
                    del decorated_function._cache[key]
            
            return result
        return decorated_function
    return decorator

def format_team_name(team_name):
    """Formata nome do time para busca consistente"""
    team_mapping = {
        'Atletico-MG': 'Atlético-MG',
        'Atletico-GO': 'Atlético-GO',
        'Atletico-PR': 'Athletico-PR',
        'Atletico Paranaense': 'Athletico-PR',
        'Atletico Mineiro': 'Atlético-MG',
        'Sao Paulo': 'São Paulo',
        'Gremio': 'Grêmio',
        'Corinthians': 'Corinthians',
        'Flamengo': 'Flamengo',
        'Palmeiras': 'Palmeiras',
        'Santos': 'Santos',
        'Vasco da Gama': 'Vasco',
        'Internacional': 'Internacional',
        'Botafogo': 'Botafogo',
        'Fluminense': 'Fluminense',
        'Bahia': 'Bahia',
        'Sport Recife': 'Sport',
        'Ceara': 'Ceará',
        'Fortaleza': 'Fortaleza',
        'Bragantino': 'Bragantino',
        'Cuiaba': 'Cuiabá'
    }
    
    return team_mapping.get(team_name, team_name)

def get_team_colors(team_name):
    """Retorna as cores do time"""
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
        'Cuiabá': {'primary': '#FFD700', 'secondary': '#00FF00'}
    }
    
    formatted_name = format_team_name(team_name)
    return TEAM_COLORS.get(formatted_name, {'primary': '#007BFF', 'secondary': '#FFFFFF'})

def safe_api_request(url, headers=None, params=None, timeout=10):
    """Faz requisição segura para APIs externas"""
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"API request failed: {url} - {str(e)}")
        return None
    except json.JSONDecodeError as e:
        current_app.logger.error(f"JSON decode error: {url} - {str(e)}")
        return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calcula distância entre duas coordenadas em km"""
    from math import radians, cos, sin, asin, sqrt
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r

def is_match_today(match_date):
    """Verifica se o jogo é hoje"""
    if isinstance(match_date, str):
        match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
    
    today = datetime.now().date()
    return match_date.date() == today

def format_match_time(match_date):
    """Formata horário do jogo"""
    if isinstance(match_date, str):
        match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
    
    return match_date.strftime('%H:%M')

def get_match_status_text(status):
    """Converte status do jogo para português"""
    status_mapping = {
        'scheduled': 'Agendado',
        'live': 'Ao Vivo',
        'finished': 'Finalizado',
        'postponed': 'Adiado',
        'cancelled': 'Cancelado',
        'suspended': 'Suspenso',
        '1H': '1º Tempo',
        '2H': '2º Tempo',
        'HT': 'Intervalo',
        'FT': 'Fim de Jogo',
        'ET': 'Prorrogação',
        'P': 'Pênaltis'
    }
    
    return status_mapping.get(status, status)