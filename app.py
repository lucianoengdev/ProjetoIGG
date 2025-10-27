import os # Novo! Para lidar com caminhos de arquivos
from flask import Flask, render_template, request, redirect # Novo! 'request' e 'redirect'

# Cria a nossa aplicação web
app = Flask(__name__)

# Configuração da pasta de uploads
# 'os.path.abspath(os.path.dirname(__file__))' pega o caminho absoluto da pasta do seu projeto
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# --- ROTA 1: A PÁGINA INICIAL ('/') ---
@app.route('/')
def index():
    return render_template('index.html')


# --- ROTA 2: O UPLOAD ('/upload') ---
# Esta rota só aceita o método 'POST', que é o que o formulário envia
@app.route('/upload', methods=['POST'])
def upload_file():
    # 1. Verificar se o arquivo veio na requisição
    if 'planilha' not in request.files:
        return "Nenhum arquivo encontrado!"

    file = request.files['planilha'] # Pega o arquivo pelo 'name' do HTML

    # 2. Se o usuário não selecionar um arquivo, o navegador envia um nome vazio
    if file.filename == '':
        return "Nenhum arquivo selecionado!"

    # 3. Pegar o número da linha inicial do formulário
    # Usamos request.form para pegar dados de texto (como o input type="number")
    linha_inicial = request.form['linha_inicial']

    # --- TESTE: Imprimir no terminal para ver se recebemos ---
    print("-----------------------------------")
    print(f"Arquivo recebido: {file.filename}")
    print(f"Linha inicial dos dados: {linha_inicial}")
    print("-----------------------------------")
    # --------------------------------------------------------

    # 4. Salvar o arquivo na pasta /uploads
    if file:
        # 'os.path.join' junta o caminho da pasta com o nome do arquivo (jeito seguro)
        caminho_seguro = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(caminho_seguro)

        # Por enquanto, vamos só dar uma resposta simples
        # No futuro, vamos redirecionar para a página de relatório:
        # return redirect('/relatorio')

        return f"Arquivo '{file.filename}' recebido com sucesso! <br> Começar a ler da linha: {linha_inicial}"


# --- INICIA O SERVIDOR ---
if __name__ == '__main__':
    app.run(debug=True)