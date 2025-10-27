from flask import Flask, render_template

# Cria a nossa aplicação web
app = Flask(__name__)

# --- ROTA 1: A PÁGINA INICIAL ('/') ---
# Define o que acontece quando alguém visita o site
@app.route('/')
def index():
    # Apenas renderiza (mostra) o arquivo HTML chamado 'index.html'
    return render_template('index.html')


# --- INICIA O SERVIDOR ---
# Permite que a gente rode o app usando "python app.py"
if __name__ == '__main__':
    app.run(debug=True)