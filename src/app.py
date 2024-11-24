import os
import sys

# Adiciona o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, request, jsonify, send_file, render_template
from src.youtube_scraper import get_youtube_channels, save_to_csv

app = Flask(__name__)

# Diretório dos CSVs
CSV_DIR = "lotes_csv"
os.makedirs(CSV_DIR, exist_ok=True)  # Garante que a pasta existe

@app.route('/')
def index():
    # Lista os arquivos CSV disponíveis
    csv_files = [f for f in os.listdir('lotes_csv') if f.endswith('.csv')]
    return render_template('index.html', csv_files=csv_files)

@app.route('/start_capturing', methods=['POST'])
def start_capturing():
    try:
        query = request.form.get("keyword")
        max_results = int(request.form.get("max_results"))
        min_subscribers = int(request.form.get("min_subscribers"))
        max_subscribers = int(request.form.get("max_subscribers"))

        # Chama a função de captura de canais
        channels = get_youtube_channels(
            query=query,
            max_results=max_results,
            min_subscribers=min_subscribers,
            max_subscribers=max_subscribers
        )

        # Salva o resultado em CSV
        filename = save_to_csv(channels)

        return jsonify({"message": "Captação de canais iniciada e CSV gerado com sucesso!", "filename": filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/list_csv', methods=['GET'])
def list_csv():
    # Lista todos os arquivos CSV no diretório
    files = [f for f in os.listdir(CSV_DIR) if f.endswith('.csv')]

    # Pega o número da página atual (padrão: 1)
    page = int(request.args.get('page', 1))
    per_page = 10  # Número de arquivos por página
    start = (page - 1) * per_page
    end = start + per_page

    # Divide a lista de arquivos em páginas
    paginated_files = files[start:end]

    # Calcula se existem páginas anteriores ou próximas
    has_next = end < len(files)
    has_prev = start > 0

    # Páginas anteriores e próximas
    next_page = page + 1 if has_next else None
    prev_page = page - 1 if has_prev else None

    return render_template(
        'list.html', 
        files=paginated_files, 
        next_page=next_page, 
        prev_page=prev_page
    )

@app.route('/download_csv/<filename>', methods=['GET'])
def download_csv(filename):
    try:
        # Caminho completo do arquivo
        filepath = os.path.join(CSV_DIR, filename)

        # Verifica se o arquivo existe
        if not os.path.exists(filepath):
            return jsonify({"error": "Arquivo não encontrado"}), 404

        # Envia o arquivo se ele existir
        return send_file(filepath, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
