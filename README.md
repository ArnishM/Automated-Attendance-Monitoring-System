# 🎓 Secure Classroom Face Monitoring & Attendance Analytics System

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5%2B-green.svg)](https://opencv.org/)
[![Dlib](https://img.shields.io/badge/Dlib-Face%20Recognition-orange.svg)](http://dlib.net/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **PL-2 (Advanced Python Laboratory) Mini Project**
> An automated classroom attendance system that uses face recognition, IP-based location verification, CSV file management, and data visualization.

---

## 📌 What This Project Does

Traditional classroom attendance is manual, slow, and prone to **proxy attendance** (one student marking for another). This system solves all three problems by:

1. **Identifying students by face** using a webcam — no manual roll call.
2. **Blocking remote marking** by verifying the machine's public IP location matches the authorized classroom city.
3. **Preventing duplicates** — a student can only be marked once per day.
4. **Generating analytics** — attendance %, defaulter lists, trends, and charts automatically after every session.

---

## 🚀 Setup & Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note on Face Recognition:** `face_recognition` requires `dlib`. On Windows, install dlib as:
> ```bash
> pip install dlib
> pip install face_recognition
> ```
> Or use a prebuilt wheel from: [z-mahmud22/Dlib_Windows_Python3.x](https://github.com/z-mahmud22/Dlib_Windows_Python3.x)

### 2. Add Student Photos
Place one clear face photo per student in the `known_faces/` folder.
Name the file exactly as the student's name in `students.json` (e.g., `Arnish.jpg`).
*(Note: Do not commit actual student photos to a public GitHub repository. This directory is ignored via `.gitignore` except for the README)*

### 3. Configure Your Classroom Location
Open `config.py` and set:
```python
ALLOWED_CITY    = "Chennai"   # Your classroom city
ALLOWED_COUNTRY = "IN"        # Country code
```

---

## 🎮 How to Run

### Live Attendance (with location check)
```bash
python main.py
```

### Demo Mode (no location check — for testing/presentation)
```bash
python main.py --demo
```

### Generate Reports Only
```bash
python main.py --report
```

### Controls (during live session)
| Key | Action |
|-----|--------|
| `SPACE` | Mark attendance for the currently recognized face |
| `R` | Toggle an on-screen display of today's attendance list |
| `Q` | End session & auto-generate visual reports |

---

## 🗂️ Project Structure

```
Attendance Monitoring System/
│
├── main.py                   ← Entry point — runs everything
├── config.py                 ← All settings in one place
├── students.json             ← Student master database
├── attendance.csv            ← Auto-generated attendance log
├── requirements.txt          ← Python dependencies
│
├── modules/
│   ├── __init__.py           
│   ├── exceptions.py         ← Custom error classes
│   ├── location_checker.py   ← IP-based classroom gate
│   ├── attendance_manager.py ← CSV read/write + duplicate prevention
│   ├── report_analyzer.py    ← Analytics using map/filter/reduce/NumPy
│   └── visualizer.py         ← Bar chart, pie chart, trend graph
│
├── known_faces/              ← Student face photos go here
│   └── README.md
│
└── reports/                  ← Auto-generated output
    ├── attendance_summary.csv
    ├── bar_chart_attendance.png
    ├── pie_chart_distribution.png
    └── trend_graph.png
```

---

## 🔐 Security Layers

1. **Location Gate**: Must be in the right city (IP check) before the webcam even opens.
2. **Face Recognition**: Only pre-registered student faces from `known_faces/` are accepted. Unknown faces show a red box but CANNOT mark attendance.
3. **Duplicate Prevention**: Same student cannot be marked twice in one day. Checked in `attendance.csv` before every write.

---

## 🧩 PL-2 Concepts Covered

| Concept | File | Usage |
|---------|------|-------|
| **OOP (Classes)** | All modules | `LocationChecker`, `AttendanceManager`, `ReportAnalyzer`, `Visualizer` |
| **Custom Exceptions** | `exceptions.py` | 5 custom exception classes |
| **File Handling** | `attendance_manager.py` | Read/write `attendance.csv` & load `students.json` |
| **`map()`** | `report_analyzer.py` | Maps every name to its attendance % |
| **`filter()`** | `report_analyzer.py` | Filters names below defaulter threshold |
| **`reduce()`** | `report_analyzer.py` | Reduces records to a date→count trend dict |
| **NumPy** | `report_analyzer.py` | Binary arrays & `np.mean()` for % calc |
| **Data Viz** | `visualizer.py` | Matplotlib & Seaborn charts (Bar, Pie, Trend) |
| **Requests API** | `location_checker.py` | Calling geolocation APIs to fetch IP data |

---

## 🔗 Architecture Diagram

```
                        ┌─────────────┐
                        │   config.py │  ← settings used by everyone
                        └──────┬──────┘
                               │ imported by all
                ┌──────────────┼────────────────────┐
                │              │                    │
         ┌──────▼──────┐ ┌────▼────────┐   ┌───────▼──────┐
         │location_    │ │attendance_  │   │report_       │
         │checker.py   │ │manager.py  │   │analyzer.py   │
         └──────┬──────┘ └────┬───────┘   └──────┬───────┘
                │             │                   │
                │             │           ┌───────▼──────┐
                │             │           │ visualizer.py│
                │             │           └──────┬───────┘
                │             │                  │
                └─────────────▼──────────────────┘
                              │
                         ┌────▼─────┐
                         │ main.py  │
                         └──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   exceptions.py    │
                    └────────────────────┘
```
