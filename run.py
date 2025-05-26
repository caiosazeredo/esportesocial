import os
from dotenv import load_dotenv
from app import app, socketio

# Carregar variáveis de ambiente
load_dotenv()

def validate_environment():
    """Valida se as variáveis essenciais estão configuradas"""
    required_vars = {
        'DATABASE_URL': 'String de conexão com o banco de dados',
        'GOOGLE_MAPS_API_KEY': 'Chave da API do Google Maps',
        'API_FUTEBOL_KEY': 'Chave da API-Futebol.com.br',
        'SECRET_KEY': 'Chave secreta da aplicação'
    }
    
    missing_vars = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing_vars.append(f"  - {var}: {description}")
    
    if missing_vars:
        print("❌ ERRO: Variáveis de ambiente obrigatórias não encontradas:")
        print("\n".join(missing_vars))
        print("\n📋 Instruções:")
        print("1. Copie .env.example para .env")
        print("2. Configure suas chaves de API no arquivo .env")
        print("3. Execute novamente")
        return False
    
    return True

def main():
    """Função principal"""
    print("🏈 EsporteSocial - Rede Social para Torcedores")
    print("=" * 50)
    
    # Validar ambiente
    if not validate_environment():
        exit(1)
    
    # Configurar porta e modo
    port = int(os.environ.get('PORT', 5000))
    env = os.environ.get('FLASK_ENV', 'development')
    debug = env == 'development'
    
    print(f"🌐 Modo: {env}")
    print(f"🚀 Servidor: http://localhost:{port}")
    print(f"🔧 Debug: {'Ativado' if debug else 'Desativado'}")
    
    if debug:
        print("\n📋 Usuários de teste:")
        print("   Email: admin@esportesocial.com | Senha: admin123")
        print("   Email: torcedor@esportesocial.com | Senha: 123456")
    
    print("\n⚽ Iniciando aplicação...")
    
    try:
        # Executar aplicação
        socketio.run(
            app, 
            debug=debug, 
            host='0.0.0.0', 
            port=port,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n👋 Aplicação encerrada pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao executar aplicação: {e}")
        exit(1)

if __name__ == '__main__':
    main()