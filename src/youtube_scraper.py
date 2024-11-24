import os
import re
import requests
import pandas as pd
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed
from config.api_keys import YOUTUBE_API_KEY

YOUTUBE_SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'
YOUTUBE_CHANNEL_URL = 'https://www.googleapis.com/youtube/v3/channels'
PROCESSED_CHANNELS_FILE = 'processed_channels.txt'

# Função para carregar IDs de canais já processados
def load_processed_channels():
    if not os.path.exists(PROCESSED_CHANNELS_FILE):
        return set()
    with open(PROCESSED_CHANNELS_FILE, 'r', encoding='utf-8') as file:
        return set(line.strip() for line in file.readlines())

# Função para salvar IDs de canais processados
def save_processed_channels(new_channels):
    with open(PROCESSED_CHANNELS_FILE, 'a', encoding='utf-8') as file:
        file.writelines(f"{channel_id}\n" for channel_id in new_channels)

# Função para extrair links e e-mails da descrição
def extract_links_and_emails(description):
    url_pattern = r'(https?://[^\s]+)'
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    links = re.findall(url_pattern, description)
    emails = re.findall(email_pattern, description)

    return {
        'Links': ', '.join(links) if links else 'Nenhum link encontrado',
        'Emails': ', '.join(emails) if emails else 'Nenhum e-mail encontrado'
    }

@retry(stop=stop_after_attempt(5), wait=wait_fixed(2))
def make_request_with_retry(url, params):
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    return response

def get_channel_statistics(channel_id):
    params = {
        'part': 'statistics,snippet',
        'id': channel_id,
        'key': YOUTUBE_API_KEY
    }
    try:
        response = make_request_with_retry(YOUTUBE_CHANNEL_URL, params)
        data = response.json()
        return data['items'][0] if 'items' in data and data['items'] else None
    except Exception as e:
        print(f"Erro ao obter estatísticas do canal {channel_id}: {e}")
        return None

def get_youtube_channels(query, max_results, min_subscribers=0, max_subscribers=None):
    processed_channels = load_processed_channels()
    channels = []
    new_processed_channels = set()
    next_page_token = None
    total_results = 0

    while total_results < max_results:
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'channel',
            'maxResults': 50,
            'key': YOUTUBE_API_KEY,
            'pageToken': next_page_token
        }
        try:
            response = make_request_with_retry(YOUTUBE_SEARCH_URL, params)
            data = response.json()
        except Exception as e:
            print(f"Erro ao buscar canais: {e}")
            break

        if 'items' not in data or not data['items']:
            break

        for item in data['items']:
            channel_id = item['snippet']['channelId']
            if channel_id in processed_channels:
                continue

            stats = get_channel_statistics(channel_id)
            if not stats:
                continue

            subscriber_count = int(stats['statistics'].get('subscriberCount', 0))
            description = stats['snippet'].get('description', '')

            extracted_data = extract_links_and_emails(description)

            if subscriber_count < min_subscribers or (max_subscribers and subscriber_count > max_subscribers):
                continue

            channels.append({
                'Nome': item['snippet']['title'],
                'URL': f'https://www.youtube.com/channel/{channel_id}',
                'Inscritos': subscriber_count,
                'Links': extracted_data['Links'],
                'Emails': extracted_data['Emails']
            })
            new_processed_channels.add(channel_id)

            # Verifica se atingiu o limite do lote atual
            if len(channels) >= max_results:
                break

        next_page_token = data.get('nextPageToken')
        total_results += len(data['items'])
        if not next_page_token or len(channels) >= max_results:
            break

    # Salva os canais processados no arquivo .txt
    save_processed_channels(new_processed_channels)
    return channels

# Função para salvar dados em um arquivo CSV por operação
def save_to_csv(data):
    """
    Salva os dados em um arquivo CSV no diretório `lotes_csv`.
    O nome do arquivo inclui a data e hora no formato desejado.
    """
    # Define o diretório para salvar os CSVs
    CSV_DIR = "lotes_csv"
    os.makedirs(CSV_DIR, exist_ok=True)  # Cria o diretório, se não existir

    # Define o padrão do nome do arquivo: data_horas.csv
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')  # Exemplo: 2024-11-20_06-45-32
    filename = f"{timestamp}.csv"
    filepath = os.path.join(CSV_DIR, filename)
    
    # Salva o DataFrame no arquivo
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    return filepath


