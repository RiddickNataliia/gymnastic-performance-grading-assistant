# Gymnastic Performance Grading Assistant (`ctai-team-project-gym-g1`)

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](#)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](#)
[![MediaPipe](https://img.shields.io/badge/Pose-MediaPipe-0097A7)](#)
[![PyTorch](https://img.shields.io/badge/Deep%20Learning-BiLSTM-EE4C2C?logo=pytorch&logoColor=white)](#)
[![Gradio](https://img.shields.io/badge/UI-Gradio-FF7C00)](#)

> **Awarded the highest grade across all class projects.**  
> Developed for **Howest University of Applied Sciences** (*Lerarenopleiding Secundair Onderwijs* — Teacher Training in Secondary Physical Education).

An end-to-end computer vision and action-recognition system that analyses video recordings of gymnastic exercises, segments execution stages, and automatically evaluates movement quality against pedagogical criteria.

---

> **Project & Repository Note**  
> This project was developed collaboratively in a student team. The initial infrastructure setup was led by my teammate, and this repository is a standalone showcase of the project.  
>  
> **My Role & Contributions:**  
> Designed and implemented the complete pose-based action recognition pipeline (MediaPipe + BiLSTM), from data collection and annotation through model training to backend integration. Built temporal stage segmentation and 5-criteria pass/fail grading models (85–91% accuracy across 464 imbalanced videos), authored client-facing recommendations for data scaling, and liaised with coaches and mentors to align evaluation requirements.

---

## Overview & Performance

* **Pipeline Accuracy:** **85–91% accuracy** across temporal phase detection and pass/fail criterion scoring.
* **Dataset:** Trained and evaluated on **464 real-world video recordings** of non-professional performers, handling class imbalance (sparse correct execution samples).
* **Target Exercises:** Handstand and Spread Jump (*Spreidsprong*).
* **Two-Stage Inference:** Combines torso-normalized pose estimation, temporal phase segmentation, and multi-criteria technique grading.

---

## Technical Architecture

The application is structured as three containerized services communicating over a dedicated Docker bridge network:

```
[ User / Browser ]
        │
        ▼
┌───────────────────────────┐
│     Gradio Web UI         │  (Port 7860)
└─────────────┬─────────────┘
              │ POST video + exercise type
              ▼
┌───────────────────────────┐      POST video       ┌───────────────────────────┐
│      Prediction API       ├──────────────────────►│  Keypoints Extraction API │
│  (BiLSTM Stage + Grading) │◄──────────────────────┤     (MediaPipe Pose)      │
└───────────────────────────┘  binary float32 array └───────────────────────────┘
```

### Services

* **Keypoints Extraction API (`keypoints-api`)**
  * Uses **MediaPipe Pose** to extract per-frame coordinates.
  * Normalizes coordinates relative to torso dimensions (invariance to subject height and camera distance).
  * Applies visibility thresholding and temporal stability filtering to minimize jitter.
  * Streams raw `float32` byte buffers with dimension metadata via a custom `X-Array-Shape` header.

* **Prediction API (`prediction-api`)**
  * **Stage 1 (Segmentation):** BiLSTM detects and segments temporal movement phases.
  * **Stage 2 (Grading):** BiLSTM + MLP classification head scores binary pass/fail outcomes across 5 criteria.
  * Supports CUDA GPU acceleration with automatic fallback to CPU.

* **Gradio Web Application (`web-app`)**
  * Interface for video uploads, criteria checklists, and real-time review.
  * Generates ZIP export packages containing:
    * Annotated evaluation video
    * Metric summary (`.csv`)
    * Diagnostic report (`.pdf`)

---

## Execution Flow & Lifecycle

```
[Upload Video] ──► [Web App] ──► [Prediction API] ──► [Keypoints API]
                                                            │
[UI Display / Export] ◄── [Score 5 Criteria] ◄── [Pose Arrays]
```

Startup dependencies are strictly enforced through Docker health checks:
```
keypoints-api (healthy) ──► prediction-api (healthy) ──► web-app
```

---

## Deployment Guide

### Prerequisites
* Docker and Docker Compose installed.

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/RiddickNataliia/gymnastic-performance-grading-assistant.git](https://github.com/RiddickNataliia/gymnastic-performance-grading-assistant.git)
   cd gymnastic-performance-grading-assistant
   ```

2. **Adjust `compose.yml` for local deployment:**  
   Remove the `caddy` service definition block from `compose.yml`:
   ```yaml
   caddy:
     image: caddy:latest
     container_name: caddy-gateway
     restart: unless-stopped
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./Caddyfile:/etc/caddy/Caddyfile
       - caddy_data:/data
       - caddy_config:/config
     depends_on:
       web:
         condition: service_healthy
     networks:
       - service-network
   ```

3. **Save `compose.yml`.**

4. **Build and launch the containers:**
   ```bash
   docker compose up --build -d
   ```

5. **Open the interface:**  
   Navigate to [http://localhost:7860](http://localhost:7860) in your browser.
