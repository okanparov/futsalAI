# 🏆 Futsal AI Player Analysis System - Proje Konteksti

## 📋 Proje Özeti
Yapay zeka tabanlı futsal (halı saha) maçı oyuncu takip ve performans analiz sistemi.
Kamera görüntüsünden gerçek zamanlı oyuncu tespiti, tracking ve detaylı istatistik analizi yapılacak.

---

## 🎯 Ana Hedefler

1. **Oyuncu Takibi (Player Tracking)**
   - YOLOv8 ile oyuncu tespiti
   - DeepSORT ile oyuncu ID takibi
   - Pozisyon coordinates kaydı

2. **Performans Metrikleri**
   - Koşu mesafesi (distance covered)
   - Top temaslı pozisyonlar
   - Pas doğruluğu (pass accuracy)
   - Pozisyon haritası (heat map)
   - Top kayıp/ele geçirme (ball loss/gain)

3. **Puan Sistemi (Rating 0-99)**
   - Genel rating
   - Position-specific stats (forvard, orta saha, defans, kaleci)
   - Karşılaştırma vs. lig ortalaması

4. **Oyun Kartı (FC27 Tarzı)**
   - Oyuncu profil kartı
   - Match statistics
   - Performance breakdown
   - Historic trends

5. **Web Dashboard**
   - Real-time monitoring
   - Post-match detailed analysis
   - Comparison tools
   - Video highlights with analytics

---

## 🛠️ Teknik Stack

### **Hardware Setup**
- **PC:** Alienware 16 Aurora AC16250
  - GPU: NVIDIA RTX 5050 (8GB VRAM)
  - CPU: Intel Core i7/i9 13th gen+
  - RAM: 32GB+
  - Storage: NVMe SSD 1TB+

- **Kamera:** Sabit profesyonel kamera (tripod + 3-4m yükseklik, 45° açı)
  - Resolüsyon: 1080p/4K 30-60fps
  - WiFi/HDMI output

### **Software Stack**
```
Python 3.13
├─ YOLOv8 (ultralytics)        → Oyuncu tespiti
├─ DeepSORT (boxmot)            → Oyuncu tracking
├─ MediaPipe                    → Pose estimation
├─ OpenCV                       → Video processing
├─ ONNX Runtime GPU             → GPU acceleration
├─ Flask                        → Web backend
├─ NumPy/Pandas                 → Data processing
└─ Scikit-learn                 → ML scoring

Frontend:
├─ HTML5 + CSS3
├─ JavaScript (vanilla/Vue.js)
└─ Chart.js / D3.js            → Visualizations
```

---

## 📊 Sistem Mimarisi

```
┌──────────────────────────────────────┐
│         Video Input (Kamera)         │
└────────────────┬─────────────────────┘
                 │
        ┌────────▼────────┐
        │  Video Capture  │
        │   (OpenCV)      │
        └────────┬────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────▼─────┐         ┌──────▼──────┐
│  YOLOv8  │         │  MediaPipe  │
│ (Players)│         │   (Pose)    │
└────┬─────┘         └──────┬──────┘
     │                      │
     └──────────┬───────────┘
                │
        ┌───────▼────────┐
        │   DeepSORT     │
        │  (Tracking)    │
        └───────┬────────┘
                │
        ┌───────▼──────────┐
        │  Data Processing │
        │ (Stats & Metrics)│
        └───────┬──────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐ ┌────▼──┐ ┌─────▼────┐
│SQLite │ │ JSON  │ │  Video   │
│Database│ │Cache │ │ Frames   │
└───────┘ └───────┘ └──────────┘
    │
    └───────────┬────────────┐
                │            │
        ┌───────▼────────┐   │
        │  Flask API     │   │
        │  (Backend)     │   │
        └───────┬────────┘   │
                │            │
        ┌───────▼────────────▼──────┐
        │   Web Dashboard (Frontend) │
        │  - Real-time monitoring   │
        │  - Match stats            │
        │  - Player cards (FC27)    │
        │  - Heat maps              │
        └────────────────────────────┘
```

---

## 📁 Dosya Yapısı

```
D:\DevOps\Apps\Futsal\
├── futsal_env/                 # Virtual environment
├── context.md                  # Bu dosya
├── config.yaml                 # Configuration file
├── models/
│   ├── yolov8n.pt             # YOLOv8 nano model
│   └── player_classifier.pkl  # Custom classifiers (opcional)
├── src/
│   ├── __init__.py
│   ├── video_processor.py     # Video input & frame extraction
│   ├── player_detector.py     # YOLOv8 + MediaPipe
│   ├── tracker.py             # DeepSORT tracking
│   ├── stats_calculator.py    # Metrics & scoring
│   ├── rating_system.py       # 0-99 puan sistemi
│   └── database.py            # SQLite operations
├── app.py                      # Flask backend
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   ├── dashboard.js
│   │   └── player_cards.js
│   └── assets/
│       └── images/
├── templates/
│   ├── index.html             # Main dashboard
│   ├── match_stats.html       # Match details
│   └── player_card.html       # FC27-style player card
├── data/
│   ├── matches.db             # SQLite database
│   ├── videos/                # Video storage
│   └── exports/               # Report exports
└── tests/
    ├── test_detection.py
    ├── test_tracking.py
    └── test_ratings.py
```

---

## 🔄 Veri Flow

### **Real-time Processing**
```
Video Frame (1080p)
    ↓
YOLOv8 Detection (25-30 FPS)
    ↓
Track ID Assignment (DeepSORT)
    ↓
Pose Estimation (MediaPipe)
    ↓
Instant Metrics Calculation
    ↓
Web Socket → Live Dashboard
```

### **Post-Match Analysis**
```
Complete Match Video
    ↓
Full Frame Processing
    ↓
All Players Tracked & Indexed
    ↓
Aggregate Statistics
    ↓
Rating Calculation (0-99)
    ↓
Position-specific Metrics
    ↓
Player Cards Generated
    ↓
Reports & Exports
```

---

## 📊 Rating System (0-99)

### **Calculation Formula**

```python
Overall_Rating = (
    0.30 * Defensive_Stats +
    0.25 * Offensive_Stats +
    0.20 * Positioning_Score +
    0.15 * Ball_Interaction +
    0.10 * Physical_Performance
) * 99
```

### **Position-Specific Weights**

**Kaleci (Goalkeeper):**
- Shot Saves: 40%
- Pass Accuracy: 30%
- Distribution: 20%
- Positioning: 10%

**Defans (Defense):**
- Tackles Won: 35%
- Interceptions: 25%
- Pass Accuracy: 20%
- Positioning: 20%

**Orta Saha (Midfielder):**
- Pass Completion: 30%
- Ball Recovery: 25%
- Positioning: 25%
- Tackles/Interceptions: 20%

**Forvard (Forward):**
- Shots on Target: 35%
- Passing Accuracy: 20%
- Ball Control: 25%
- Positioning: 20%

---

## 🎮 Key Features

### **Phase 1: MVP**
- ✅ Video capture & processing
- ✅ Player detection & tracking
- ✅ Basic statistics (distance, positions)
- ✅ Simple web dashboard
- ✅ Basic rating system (0-99)

### **Phase 2: Enhanced**
- 📊 Detailed position analytics
- 🎯 Ball possession tracking
- 🔄 Pass accuracy calculation
- 🎬 Highlight detection
- 📈 Historic comparisons

### **Phase 3: Advanced**
- 🤖 AI tactical analysis
- 📱 Mobile app
- 🎥 Multi-angle processing
- 🔔 Real-time alerts
- 📊 Advanced ML insights

---

## 🚀 Development Roadmap

### **Sprint 1: Core Pipeline (Week 1-2)**
- [ ] Video input module
- [ ] YOLOv8 + MediaPipe integration
- [ ] DeepSORT tracker setup
- [ ] Basic database schema
- [ ] Flask API skeleton

### **Sprint 2: Analytics (Week 3-4)**
- [ ] Stats calculation engine
- [ ] Rating algorithm
- [ ] Position-specific metrics
- [ ] Data aggregation

### **Sprint 3: Frontend (Week 5-6)**
- [ ] Web dashboard
- [ ] Player card UI (FC27 style)
- [ ] Real-time charts
- [ ] Match history

### **Sprint 4: Polish & Testing (Week 7-8)**
- [ ] Performance optimization
- [ ] Bug fixes
- [ ] User testing
- [ ] Documentation

---

## 💾 Database Schema (SQLite)

```sql
-- Players
CREATE TABLE players (
    id INTEGER PRIMARY KEY,
    match_id INTEGER,
    team_id INTEGER,
    player_name TEXT,
    position TEXT,
    jersey_number INTEGER,
    player_color TEXT
);

-- Detections (per frame)
CREATE TABLE detections (
    id INTEGER PRIMARY KEY,
    frame_id INTEGER,
    player_id INTEGER,
    bbox_x REAL,
    bbox_y REAL,
    confidence REAL,
    timestamp REAL
);

-- Match Stats
CREATE TABLE match_stats (
    id INTEGER PRIMARY KEY,
    match_id INTEGER,
    player_id INTEGER,
    distance_covered REAL,
    pass_attempts INTEGER,
    pass_success INTEGER,
    ball_touches INTEGER,
    tackles INTEGER,
    interceptions INTEGER,
    rating REAL
);

-- Matches
CREATE TABLE matches (
    id INTEGER PRIMARY KEY,
    date TIMESTAMP,
    team1 TEXT,
    team2 TEXT,
    venue TEXT,
    video_path TEXT,
    processed BOOLEAN
);
```

---

## 🔑 Key APIs

### **Video Processing**
```python
processor = VideoProcessor(video_path)
frames = processor.extract_frames(fps=30)
```

### **Detection & Tracking**
```python
detector = PlayerDetector()
tracker = DeepSORT()

for frame in frames:
    detections = detector.detect(frame)  # YOLOv8
    poses = detector.estimate_pose(frame) # MediaPipe
    tracks = tracker.update(detections)
```

### **Statistics**
```python
stats = StatsCalculator()
match_data = stats.process_tracks(tracks, frames)
ratings = RatingSystem().calculate(match_data)
```

---

## 🌐 API Endpoints (Flask)

```
POST   /api/upload-video         # Video yükle
POST   /api/process-match        # Maçı işle
GET    /api/match/<id>          # Match detayları
GET    /api/player/<id>/stats   # Oyuncu istatistikleri
GET    /api/match/<id>/ratings  # Tüm oyuncu puanları
GET    /api/dashboard           # Dashboard verisi
```

---

## 📝 Environment & Setup

### **Installed Libraries**
- ✅ YOLOv8 (ultralytics 8.4.172)
- ✅ MediaPipe 1.0.1
- ✅ DeepSORT (boxmot 25.0.0)
- ✅ ONNX Runtime GPU 1.30.0
- ✅ OpenCV 4.14.0
- ✅ Flask 3.1.3
- ✅ NumPy 2.5.3
- ✅ Pandas 2.3.3
- ✅ Scikit-learn 1.9.1

### **GPU Status**
- ONNX Providers: TensorrtExecutionProvider, CUDAExecutionProvider, CPUExecutionProvider
- YOLOv8: Ready with ONNX GPU support
- Processing: CPU + GPU optimization

---

## 👨‍💻 Developer Context

**Main Focus:** Build end-to-end futsal analytics system with:
1. Robust player tracking
2. Accurate performance metrics
3. Beautiful FC27-style player cards
4. Real-time + post-match analysis
5. Scalable architecture for future enhancements

**Tech Preference:** Python backend + vanilla JS frontend (minimal dependencies)

**GPU Architecture:** ONNX Runtime GPU for efficient inference, avoiding torch GPU compatibility issues with RTX 5050

---

## 📞 Next Steps

1. **Claude Code Setup** - Move to Claude Code for rapid development
2. **Phase 1 Implementation** - Core video processing pipeline
3. **Real-time Testing** - Test with sample video
4. **Dashboard Development** - Web interface
5. **Integration & Polish** - Final optimizations

---

**Last Updated:** October 3, 2026
**Status:** Ready for Claude Code implementation
**Python Version:** 3.13
**Working Directory:** D:\DevOps\Apps\Futsal
