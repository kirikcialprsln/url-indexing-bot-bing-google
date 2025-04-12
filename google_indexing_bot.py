import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging
from datetime import datetime, timedelta

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.FileHandler('indexing_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('IndexingBot')

# URL gönderimi için minimum bekleme süresi (saat)
MIN_HOURS_BETWEEN_SUBMISSIONS = 24

class URLTracker:
    def __init__(self, filename='sent_urls.json'):
        self.logger = logging.getLogger('URLTracker')
        self.filename = filename
        self.sent_urls = self._load_sent_urls()

    def _load_sent_urls(self):
        """Gönderilen URL'leri yükle."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logger.info(f"URL geçmişi yüklendi: {len(data)} URL bulundu")
                    return data
            except Exception as e:
                self.logger.error(f"URL geçmişi yüklenirken hata: {str(e)}")
                return {}
        self.logger.info("URL geçmişi bulunamadı, yeni dosya oluşturulacak")
        return {}

    def _save_sent_urls(self):
        """Gönderilen URL'leri kaydet."""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(self.sent_urls, f, ensure_ascii=False, indent=2)
            self.logger.info(f"URL geçmişi güncellendi: {len(self.sent_urls)} URL kaydedildi")
        except Exception as e:
            self.logger.error(f"URL geçmişi kaydedilirken hata: {str(e)}")

    def can_submit_url(self, url: str) -> tuple[bool, str, dict]:
        """URL'nin gönderilebilir olup olmadığını kontrol et."""
        status_info = {
            "last_submission": None,
            "hours_since_last": None,
            "remaining_hours": None
        }

        if url not in self.sent_urls:
            self.logger.info(f"Yeni URL: {url}")
            return True, "", status_info

        last_submission = datetime.fromisoformat(self.sent_urls[url])
        hours_since_last = (datetime.now() - last_submission).total_seconds() / 3600
        
        status_info.update({
            "last_submission": last_submission.strftime('%d.%m.%Y %H:%M:%S'),
            "hours_since_last": round(hours_since_last, 2),
            "remaining_hours": round(max(0, MIN_HOURS_BETWEEN_SUBMISSIONS - hours_since_last), 2)
        })

        if hours_since_last < MIN_HOURS_BETWEEN_SUBMISSIONS:
            remaining_hours = MIN_HOURS_BETWEEN_SUBMISSIONS - hours_since_last
            message = f"Bu URL {remaining_hours:.1f} saat sonra tekrar gönderilebilir"
            self.logger.warning(f"URL tekrarı engellendi: {url} - {message}")
            return False, message, status_info

        self.logger.info(f"URL tekrar gönderilebilir: {url} - Son gönderimden {hours_since_last:.1f} saat geçmiş")
        return True, "", status_info

    def mark_url_submitted(self, url: str):
        """URL'yi gönderildi olarak işaretle."""
        current_time = datetime.now().isoformat()
        self.sent_urls[url] = current_time
        self.logger.info(f"URL kaydedildi: {url} - Zaman: {current_time}")
        self._save_sent_urls()

def get_indexing_service():
    """Google Indexing API servisini başlat."""
    try:
        # Kimlik bilgilerini yükle
        credentials = service_account.Credentials.from_service_account_file(
            'service-account.json',
            scopes=['https://www.googleapis.com/auth/indexing']
        )
        
        # Servisi oluştur
        service = build('indexing', 'v3', credentials=credentials)
        logger.info("Google Indexing API servisi başarıyla başlatıldı")
        return service
        
    except Exception as e:
        logger.error(f"Servis başlatma hatası: {str(e)}")
        raise

def request_indexing(service, url: str, url_tracker: URLTracker, type_str: str = "URL_UPDATED") -> dict:
    """URL'yi indexleme için gönder."""
    try:
        # URL'nin gönderilebilir olup olmadığını kontrol et
        can_submit, message, status_info = url_tracker.can_submit_url(url)
        
        result = {
            "url": url,
            "timestamp": datetime.now().strftime('%d.%m.%Y %H:%M:%S'),
            "status_info": status_info
        }

        if not can_submit:
            result.update({
                "status": "skipped",
                "message": message
            })
            return result

        response = service.urlNotifications().publish(
            body={
                "url": url,
                "type": type_str
            }
        ).execute()
        
        # Başarılı gönderim sonrası URL'yi kaydet
        url_tracker.mark_url_submitted(url)
        
        result.update({
            "status": "success",
            "notification_type": type_str,
            "response": response
        })
        
        logger.info(f"URL başarıyla gönderildi: {url}")
        return result

    except Exception as e:
        error_message = str(e)
        logger.error(f"İndeksleme hatası - URL: {url}, Hata: {error_message}")
        
        result.update({
            "status": "error",
            "error": error_message
        })
        return result

def filter_submittable_urls(urls: list[str], url_tracker: URLTracker) -> list[tuple[str, str]]:
    """Gönderilebilir URL'leri filtrele ve her URL için durumu döndür."""
    results = []
    for url in urls:
        can_submit, message, _ = url_tracker.can_submit_url(url)
        if not can_submit:
            results.append((url, message))
    return results

if __name__ == "__main__":
    try:
        # URL takipçisini başlat
        url_tracker = URLTracker()
        
        # Servis başlat
        service = get_indexing_service()
        
        # urls.json dosyasından URL'leri oku
        if os.path.exists('urls.json'):
            with open('urls.json', 'r', encoding='utf-8') as f:
                urls = json.load(f)
                logger.info(f"URLs loaded from urls.json: {len(urls)} URLs found")
                
            results = []
            for url in urls:
                try:
                    result = request_indexing(service, url, url_tracker)
                    results.append(result)
                except Exception as e:
                    logger.error(f"URL işleme hatası: {url} - {str(e)}")
                    results.append({
                        "url": url,
                        "status": "error",
                        "error": str(e),
                        "timestamp": datetime.now().strftime('%d.%m.%Y %H:%M:%S')
                    })
            
            # Sonuçları kaydet
            filename = f'results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to {filename}")
        else:
            logger.error("urls.json dosyası bulunamadı")
            
    except Exception as e:
        logger.error(f"Genel hata: {str(e)}") 