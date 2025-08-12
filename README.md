# 📈 Stock Indices RSS Feed

A lightweight Python + Flask service that fetches **stock market indices** and serves them in an **RSS feed**.

## Features
- **On-demand updates** — data is fetched only when requested via `/rss` endpoint (cached for 60 minutes)
- **Daily, Monthly, and Yearly returns** for each index
- **Color-coded returns**: green for positive, red for negative
- **RSS GUID** that changes only when data changes (helps feed readers detect updates)

---

## 📦 Running Locally

### 1. Install dependencies
pip install -r requirements.txt

### 2. Start the server
python main.py

### 3. Access the RSS feed
Open http://localhost:5000/rss in your browser or RSS reader.

---

## 🐳 Running with Docker

### 1. Build the image
docker build -t stock-rss .

### 2. Run the container
docker run -d -p 5000:5000 stock-rss

### 3. Access the RSS feed
Visit http://localhost:5000/rss.

---

## 📤 Running from GitHub Container Registry

### Pull and run:
docker pull ghcr.io/gauravdash/stock-rss:latest
docker run -d -p 5000:5000 ghcr.io/<your-username>/stock-rss:latest

---

## ⚙ Configuration

You can modify the `INDICES` dictionary in `main.py` to add or remove stock indices.  
Symbols must match those on Yahoo Finance (https://finance.yahoo.com/).

Example:
INDICES = {
    "FTSE 100": "^FTSE",
    "S&P 500": "^GSPC",
    "Nifty 50": "^NSEI",
    "NASDAQ": "^IXIC"
}

---

## 📄 License
This project is licensed under the GNU General Public License v3.0 (GPLv3).  
You may copy, distribute, and modify the software as long as you track changes/dates in source files.  
Any modifications to this code base must also be made available under the GPLv3.

Full license text: https://www.gnu.org/licenses/gpl-3.0.en.html


