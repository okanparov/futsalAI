# Futsal AI Player Analysis System

Kamera görüntüsünden oyuncu tespiti, takibi ve performans analizi yapan futsal sistemi.
Ayrıntılı proje bağlamı için `context.md` dosyasına bakın.

## Durum

| Bileşen | Durum |
|---|---|
| Video okuma (OpenCV) | Çalışıyor, testli |
| Oyuncu tespiti (YOLOv8) | Yazıldı, **gerçek modelle denenmedi** |
| Poz tahmini (MediaPipe) | Yazıldı, **denenmedi** |
| Takip | Basit IoU takipçisi. DeepSORT (boxmot) **bağlı değil** |
| İstatistik | Mesafe, ısı haritası, saha kapsamı |
| Puan sistemi (0-99) | Çalışıyor; şu an yalnızca kapsam + mesafeye dayanıyor |
| Web arayüzü | Maç listesi, maç detayı, oyuncu kartı |
| Pas / top teması / tackle | Yok (top tespiti gerekir, Faz 2) |
| Canlı izleme (WebSocket) | Yok |

## Kurulum

```bash
python -m venv futsal_env
futsal_env\Scripts\activate        # Linux/macOS: source futsal_env/bin/activate
pip install -r requirements.txt
```

`models/yolov8n.pt` dosyasını `models/` klasörüne koyun (git'e eklenmez, `.gitignore`'da).
Sürüm uyumsuzluğu olursa `requirements.txt`'teki paketleri tek tek kurun; sürümler sabitlenmemiştir.

## Çalıştırma

```bash
python app.py        # http://127.0.0.1:5000
```

1. Ana sayfadan maç videosunu yükleyin.
2. "İşle" düğmesine basın (YOLOv8 kurulu olmalı).
3. İşlenen maçın detayından oyuncu kartlarına gidin.

## Testler

```bash
pytest
```

Testler YOLOv8/MediaPipe gerektirmez; sahte dedektör ve sentetik video kullanır.

## Ayarlar (`config.yaml`)

Model yolu, güven eşiği, veritabanı yolu ve sunucu adresi buradan değişir.
Saha boyutu (varsayılan 40x20 m) `src/pipeline.py` içindeki `court_size_m` parametresidir.

## Bilinen sınırlamalar

- **Mesafe yaklaşıktır.** Piksel konumu metreye düz oranla çevriliyor; perspektif düzeltmesi
  (homografi) yok. Kamera eğikse mesafeler sapar.
- **Puan sınırlı.** Top verisi olmadığından yalnızca saha kapsamı ve koşu mesafesi kullanılıyor.
  Mesafe referansı (3000 m = tam puan) tahmindir, gerçek verilerle ayarlanmalı.
- **Pozisyon otomatik bilinmiyor**; tüm oyuncular genel formülle puanlanır.
- **Oyuncu kimliği:** Takip kimlikleri kişiye değil iz'e bağlıdır; oyuncu kadrajdan çıkıp
  dönerse yeni kimlik alabilir. Takım/forma eşleştirmesi yok.
- **Grafikler** Chart.js'i CDN'den yükler (internet gerekir).
- Flask geliştirme sunucusu kullanılır; üretim için uygun değildir.

## Yapı

```
app.py            Flask uygulaması ve API
src/              video, tespit, takip, istatistik, puan, veritabanı, pipeline
templates/        HTML şablonları
static/           CSS ve JS
tests/            pytest testleri
```
