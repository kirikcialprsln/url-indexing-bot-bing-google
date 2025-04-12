from flask import Flask, render_template, request, redirect, url_for, jsonify
from google_indexing_bot import (
    get_indexing_service,
    request_indexing,
    URLTracker as GoogleURLTracker
)
from bing_indexing_bot import (
    request_bing_indexing,
    BingURLTracker
)
import threading
import json
import os
from datetime import datetime
import logging
import time
import sys
import math
import glob

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Maksimum istek boyutunu artır (16GB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB

# UTF-8 encoding for console output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('web_panel.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('WebPanel')

# Global processing status
processing_status = {
    'is_processing': False,
    'processed_urls': 0,
    'total_urls': 0,
    'current_batch': 0,
    'total_batches': 0,
    'current_action': '',
    'success_count': 0,
    'skipped_count': 0,
    'error_count': 0,
    'error': None,
    'results': [],
    'skipped_urls': [],
    'success_urls': [],
    'error_urls': [],
    'is_completed': False,
    'completion_time': None,
    'limit_reached': False,
    'using_bing': False,
    'remaining_urls': [],
    'remaining_count': 0
}

# Bing işlem durumu
bing_processing_status = {
    'is_processing': False,
    'processed_urls': 0,
    'total_urls': 0,
    'current_batch': 0,
    'total_batches': 0,
    'current_action': '',
    'success_count': 0,
    'skipped_count': 0,
    'error_count': 0,
    'error': None,
    'results': [],
    'skipped_urls': [],
    'success_urls': [],
    'error_urls': [],
    'is_completed': False,
    'completion_time': None,
    'limit_reached': False,
    'remaining_urls': [],
    'remaining_count': 0
}

# Optimize batch processing settings
BATCH_SIZE = 500    # Her grupta 500 URL
URL_DELAY = 0.2    # URL'ler arası 0.2 saniye
BATCH_DELAY = 1    # Gruplar arası 1 saniye

# URL takipçileri
google_tracker = GoogleURLTracker()
bing_tracker = BingURLTracker()

def validate_urls(urls: list[str]) -> list[str]:
    """URL'leri doğrula ve temizle."""
    valid_urls = []
    for url in urls:
        url = url.strip()
        if url and (url.startswith('http://') or url.startswith('https://')):
            valid_urls.append(url)
    return valid_urls

def process_urls_background(urls: list[str]):
    """URL'leri arka planda işle ve durumu güncelle."""
    global processing_status
    
    try:
        # Service'i başlat
        service = get_indexing_service()
        
        # URL'leri doğrula
        valid_urls = validate_urls(urls)
        if not valid_urls:
            processing_status['error'] = "Geçerli URL bulunamadı"
            processing_status['is_processing'] = False
            return
        
        # Batch hesaplamaları
        total_urls = len(valid_urls)
        total_batches = math.ceil(total_urls / BATCH_SIZE)
        
        processing_status.update({
            'is_processing': True,
            'is_completed': False,
            'processed_urls': 0,
            'total_urls': total_urls,
            'current_batch': 0,
            'total_batches': total_batches,
            'success_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'results': [],
            'skipped_urls': [],
            'success_urls': [],
            'error_urls': [],
            'current_action': 'İşlem başlatılıyor...',
            'limit_reached': False
        })
        
        # URL'leri gruplar halinde işle
        results = []
        for batch_index in range(total_batches):
            processing_status['current_batch'] = batch_index + 1
            start_idx = batch_index * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_urls)
            batch_urls = valid_urls[start_idx:end_idx]
            
            processing_status['current_action'] = f"Grup {batch_index + 1}/{total_batches} işleniyor • Her URL arası {URL_DELAY} saniye bekleniyor"
            logger.info(f"Grup {batch_index + 1}/{total_batches} başladı")
            
            for url in batch_urls:
                try:
                    # URL'yi indexlemeye gönder
                    result = request_indexing(service, url, google_tracker)
                    
                    results.append(result)
                    processing_status['processed_urls'] += 1
                    
                    # API limit kontrolü
                    if result.get('status') == 'error' and 'quota' in str(result.get('error', '')).lower():
                        processing_status['limit_reached'] = True
                        processing_status['current_action'] = "Google API limiti aşıldı! İşlem durduruluyor..."
                        logger.warning("Google API limiti aşıldı, işlem durduruluyor")
                        
                        # Kalan URL'leri kaydet
                        remaining_urls = valid_urls[processing_status['processed_urls']:]
                        processing_status['remaining_urls'] = remaining_urls
                        processing_status['remaining_count'] = len(remaining_urls)
                        
                        # Sonuçları kaydet ve işlemi sonlandır
                        save_results(results)
                        return
                    
                    # Sonuca göre sayaçları güncelle
                    if result['status'] == 'success':
                        processing_status['success_count'] += 1
                        processing_status['success_urls'].append(url)
                        logger.info(f"URL başarıyla gönderildi: {url}")
                    elif result['status'] == 'skipped':
                        processing_status['skipped_count'] += 1
                        processing_status['skipped_urls'].append({
                            'url': url,
                            'reason': result['message']
                        })
                        logger.warning(f"URL atlandı: {url} - {result['message']}")
                    else:  # error
                        processing_status['error_count'] += 1
                        processing_status['error_urls'].append({
                            'url': url,
                            'error': result.get('error', 'Bilinmeyen hata')
                        })
                        logger.error(f"URL hatası: {url} - {result.get('error', 'Bilinmeyen hata')}")
                    
                    # Her URL işleminden sonra bekle
                    if processing_status['processed_urls'] < total_urls:
                        processing_status['current_action'] = f"URL işlendi, {URL_DELAY} saniye bekleniyor... ({processing_status['processed_urls']}/{total_urls})"
                        time.sleep(URL_DELAY)
                    
                except Exception as url_error:
                    error_message = str(url_error)
                    logger.error(f"URL işleme hatası: {url} - {error_message}")
                    results.append({
                        'url': url,
                        'status': 'error',
                        'error': error_message,
                        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    })
                    processing_status['error_count'] += 1
                    processing_status['error_urls'].append({
                        'url': url,
                        'error': error_message
                    })
            
            # Grup tamamlandı, sonraki grup için bekle
            if batch_index < total_batches - 1:
                processing_status['current_action'] = f"Grup {batch_index + 1} tamamlandı • Sonraki grup için {BATCH_DELAY} saniye bekleniyor..."
                logger.info(f"Grup {batch_index + 1} tamamlandı, {BATCH_DELAY} saniye bekleniyor")
                time.sleep(BATCH_DELAY)
        
        save_results(results)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"İşlem hatası: {error_message}")
        processing_status.update({
            'is_processing': False,
            'is_completed': True,
            'error': error_message,
            'current_action': 'Hata oluştu!'
        })

def save_results(results):
    """Sonuçları kaydet ve durumu güncelle."""
    # Sonuçları kaydet
    filename = f'history_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Sonuçlar kaydedildi: {filename}")
    
    # İşlem tamamlandı
    completion_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    processing_status.update({
        'is_processing': False,
        'is_completed': True,
        'completion_time': completion_time,
        'current_action': 'Günlük limit aşıldı!' if processing_status.get('limit_reached') else 'İşlem tamamlandı!',
        'error': None,
        'results': results
    })
    logger.info("Tüm işlem tamamlandı" + (" (Limit aşıldı)" if processing_status.get('limit_reached') else ""))

def process_bing_urls_background(urls: list[str]):
    """URL'leri Bing API ile arka planda işle."""
    global bing_processing_status
    
    try:
        # URL'leri doğrula
        valid_urls = validate_urls(urls)
        if not valid_urls:
            bing_processing_status['error'] = "Geçerli URL bulunamadı"
            bing_processing_status['is_processing'] = False
            return
        
        # Batch hesaplamaları
        total_urls = len(valid_urls)
        total_batches = math.ceil(total_urls / BATCH_SIZE)
        
        bing_processing_status.update({
            'is_processing': True,
            'is_completed': False,
            'processed_urls': 0,
            'total_urls': total_urls,
            'current_batch': 0,
            'total_batches': total_batches,
            'success_count': 0,
            'skipped_count': 0,
            'error_count': 0,
            'results': [],
            'skipped_urls': [],
            'success_urls': [],
            'error_urls': [],
            'current_action': 'İşlem başlatılıyor...',
            'limit_reached': False
        })
        
        # URL'leri gruplar halinde işle
        results = []
        for batch_index in range(total_batches):
            bing_processing_status['current_batch'] = batch_index + 1
            start_idx = batch_index * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, total_urls)
            batch_urls = valid_urls[start_idx:end_idx]
            
            bing_processing_status['current_action'] = f"Grup {batch_index + 1}/{total_batches} işleniyor • Her URL arası {URL_DELAY} saniye bekleme"
            logger.info(f"Grup {batch_index + 1}/{total_batches} başladı (Bing)")
            
            for url in batch_urls:
                try:
                    # URL'yi indexlemeye gönder
                    result = request_bing_indexing(url, bing_tracker)
                    
                    results.append(result)
                    bing_processing_status['processed_urls'] += 1
                    
                    # API limit kontrolü
                    if result.get('status') == 'error' and 'quota' in str(result.get('error', '')).lower():
                        bing_processing_status['limit_reached'] = True
                        bing_processing_status['current_action'] = "Bing API limiti aşıldı! İşlem durduruluyor..."
                        logger.warning("Bing API limiti aşıldı, işlem durduruluyor")
                        
                        # Kalan URL'leri kaydet
                        remaining_urls = valid_urls[bing_processing_status['processed_urls']:]
                        bing_processing_status['remaining_urls'] = remaining_urls
                        bing_processing_status['remaining_count'] = len(remaining_urls)
                        
                        # Sonuçları kaydet ve işlemi sonlandır
                        save_bing_results(results)
                        return
                    
                    # Sonuca göre sayaçları güncelle
                    if result['status'] == 'success':
                        bing_processing_status['success_count'] += 1
                        bing_processing_status['success_urls'].append(url)
                        logger.info(f"URL başarıyla gönderildi (Bing): {url}")
                    elif result['status'] == 'skipped':
                        bing_processing_status['skipped_count'] += 1
                        bing_processing_status['skipped_urls'].append({
                            'url': url,
                            'reason': result['message']
                        })
                        logger.warning(f"URL atlandı (Bing): {url} - {result['message']}")
                    else:  # error
                        bing_processing_status['error_count'] += 1
                        bing_processing_status['error_urls'].append({
                            'url': url,
                            'error': result.get('error', 'Bilinmeyen hata')
                        })
                        logger.error(f"URL hatası (Bing): {url} - {result.get('error', 'Bilinmeyen hata')}")
                    
                    # Her URL işleminden sonra bekle
                    if bing_processing_status['processed_urls'] < total_urls:
                        bing_processing_status['current_action'] = f"URL işlendi, {URL_DELAY} saniye bekleniyor... ({bing_processing_status['processed_urls']}/{total_urls})"
                        time.sleep(URL_DELAY)
                    
                except Exception as url_error:
                    error_message = str(url_error)
                    logger.error(f"URL işleme hatası (Bing): {url} - {error_message}")
                    results.append({
                        'url': url,
                        'status': 'error',
                        'error': error_message,
                        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    })
                    bing_processing_status['error_count'] += 1
                    bing_processing_status['error_urls'].append({
                        'url': url,
                        'error': error_message
                    })
            
            # Grup tamamlandı, sonraki grup için bekle
            if batch_index < total_batches - 1:
                bing_processing_status['current_action'] = f"Grup {batch_index + 1} tamamlandı • Sonraki grup için {BATCH_DELAY} saniye bekleniyor..."
                logger.info(f"Grup {batch_index + 1} tamamlandı (Bing), {BATCH_DELAY} saniye bekleniyor")
                time.sleep(BATCH_DELAY)
        
        save_bing_results(results)
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"İşlem hatası (Bing): {error_message}")
        bing_processing_status.update({
            'is_processing': False,
            'is_completed': True,
            'error': error_message,
            'current_action': 'Hata oluştu!'
        })

def save_bing_results(results):
    """Bing sonuçlarını kaydet ve durumu güncelle."""
    # Sonuçları kaydet
    filename = f'history_{datetime.now().strftime("%Y%m%d_%H%M%S")}_bing.json'
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Bing sonuçları kaydedildi: {filename}")
    
    # İşlem tamamlandı
    completion_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
    bing_processing_status.update({
        'is_processing': False,
        'is_completed': True,
        'completion_time': completion_time,
        'current_action': 'Günlük limit aşıldı!' if bing_processing_status.get('limit_reached') else 'İşlem tamamlandı!',
        'error': None,
        'results': results
    })
    logger.info("Bing işlemi tamamlandı" + (" (Limit aşıldı)" if bing_processing_status.get('limit_reached') else ""))

def chunk_urls(urls: list[str], chunk_size: int = 1000) -> list[list[str]]:
    """URL'leri daha küçük gruplara böl."""
    return [urls[i:i + chunk_size] for i in range(0, len(urls), chunk_size)]

def process_urls_in_memory(urls: list[str]) -> list[str]:
    """URL'leri bellek içinde işle ve temizle."""
    return [url.strip() for url in urls if url.strip() and (url.startswith('http://') or url.startswith('https://'))]

@app.route('/', methods=['GET', 'POST'])
def index():
    """Ana sayfa ve URL işleme."""
    if request.method == 'POST':
        urls = request.form.get('urls', '').split('\n')
        urls = validate_urls(urls)
        
        if not urls:
            logger.warning("Geçerli URL girilmedi")
            return render_template('index.html', error="Lütfen geçerli URL'ler girin (http:// veya https:// ile başlamalı)")
        
        logger.info(f"URL gönderimi başlatıldı: {len(urls)} URL")
        
        # Arka plan işlemi başlat
        thread = threading.Thread(
            target=process_urls_background,
            args=(urls,)
        )
        thread.daemon = True
        thread.start()
        
        return redirect(url_for('processing_status_page'))
    
    return render_template('index.html', 
                         processing_status=processing_status,
                         current_year=datetime.now().year)

@app.route('/processing_status')
def processing_status_page():
    """İşlem durumu sayfası."""
    return render_template('processing_status.html')

@app.route('/api/status')
def get_status():
    """API durumu endpoint'i."""
    return jsonify({
        'status': 'error' if processing_status['error'] else 'success',
        'processing': processing_status,
        'error': processing_status['error']
    })

@app.route('/bing', methods=['GET', 'POST'])
def bing():
    """Bing URL işleme sayfası."""
    if request.method == 'POST':
        try:
            # URL'leri bellek içinde işle
            urls = process_urls_in_memory(request.form.get('urls', '').split('\n'))
            
            if not urls:
                logger.warning("Geçerli URL girilmedi (Bing)")
                return render_template('bing.html', error="Lütfen geçerli URL'ler girin (http:// veya https:// ile başlamalı)")
            
            # URL'leri daha küçük gruplara böl
            url_chunks = chunk_urls(urls)
            logger.info(f"Bing URL gönderimi başlatıldı: {len(urls)} URL ({len(url_chunks)} grup)")
            
            # Her grup için ayrı işlem başlat
            for i, chunk in enumerate(url_chunks):
                thread = threading.Thread(
                    target=process_bing_urls_background,
                    args=(chunk,)
                )
                thread.daemon = True
                thread.start()
                logger.info(f"Grup {i+1}/{len(url_chunks)} başlatıldı ({len(chunk)} URL)")
            
            return redirect(url_for('bing_processing_status_page'))
        except Exception as e:
            logger.error(f"URL gönderimi hatası: {str(e)}")
            return render_template('bing.html', error=f"URL'ler işlenirken bir hata oluştu: {str(e)}")
    
    return render_template('bing.html', 
                         processing_status=bing_processing_status,
                         current_year=datetime.now().year)

@app.route('/bing/processing_status')
def bing_processing_status_page():
    """Bing işlem durumu sayfası."""
    return render_template('bing.html', 
                         processing_status=bing_processing_status,
                         current_year=datetime.now().year)

@app.route('/api/bing/status')
def get_bing_status():
    """Bing API durumu endpoint'i."""
    return jsonify({
        'status': 'error' if bing_processing_status['error'] else 'success',
        'processing': bing_processing_status,
        'error': bing_processing_status['error']
    })

@app.route('/history')
def history():
    """Display URL submission history."""
    try:
        # Load history from JSON files
        history_entries = []
        
        # Tüm geçmiş dosyalarını bul (hem Google hem Bing)
        history_files = glob.glob('history_*.json')
        results_files = glob.glob('results_*.json')  # Eski dosyaları da kontrol et
        bing_results_files = glob.glob('bing_results_*.json')  # Eski Bing dosyalarını da kontrol et
        
        all_files = history_files + results_files + bing_results_files
        
        for file_path in sorted(all_files, reverse=True):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    entries = json.load(f)
                    if isinstance(entries, list):
                        # Her girişe kaynak bilgisi ekle
                        for entry in entries:
                            entry['source'] = 'Bing' if 'bing' in file_path.lower() else 'Google'
                        history_entries.extend(entries)
                    else:
                        entries['source'] = 'Bing' if 'bing' in file_path.lower() else 'Google'
                        history_entries.append(entries)
            except Exception as e:
                logger.error(f"Error reading history file {file_path}: {e}")
        
        # Format timestamps and sort by most recent first
        for entry in history_entries:
            if isinstance(entry.get('timestamp'), str):
                try:
                    dt = datetime.strptime(entry['timestamp'], '%d.%m.%Y %H:%M:%S')
                    entry['timestamp'] = dt.strftime('%d.%m.%Y %H:%M:%S')
                except:
                    pass  # Keep original timestamp if parsing fails
        
        # Sort by timestamp (most recent first)
        history_entries.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return render_template(
            'history.html',
            history=history_entries
        )
        
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return render_template(
            'history.html',
            history=[],
            error="Geçmiş yüklenirken bir hata oluştu."
        )

@app.errorhandler(413)
def request_entity_too_large(error):
    """Büyük istek hatası için özel hata sayfası."""
    logger.error("İstek boyutu çok büyük (413)")
    return render_template('error.html', 
                         error="Gönderilen veri çok büyük. Lütfen URL'leri daha küçük gruplar halinde gönderin.",
                         current_year=datetime.now().year), 413

if __name__ == '__main__':
    app.run(debug=True) 