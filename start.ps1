#!/usr/bin/env powershell
# Quick Start Script for IP Project
# This script sets up and starts the entire project locally

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "IP Project - Local Development Startup" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/4] Checking prerequisites..." -ForegroundColor Yellow
$python_ver = python --version 2>&1
$node_ver = npm --version 2>&1

if ($python_ver -and $node_ver) {
    Write-Host "✅ Python: $python_ver" -ForegroundColor Green
    Write-Host "✅ Node.js/npm: $node_ver" -ForegroundColor Green
} else {
    Write-Host "❌ Missing dependencies. Please install Python 3.11+ and Node.js 16+" -ForegroundColor Red
    exit 1
}

# Backend setup
Write-Host ""
Write-Host "[2/4] Setting up backend..." -ForegroundColor Yellow
cd backend
if (Test-Path venv) {
    Write-Host "✅ Virtual environment exists" -ForegroundColor Green
    Write-Host "📦 Activating and installing dependencies..." -ForegroundColor Cyan
    & .\venv\Scripts\pip.exe install -r requirements.txt -q 2>&1 | Out-Null
    Write-Host "✅ Backend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠️  Virtual environment not found. Run setup.sh first." -ForegroundColor Red
    exit 1
}

# Check database
Write-Host ""
Write-Host "[3/4] Checking database..." -ForegroundColor Yellow
if (Test-Path workflow.db) {
    Write-Host "✅ Database exists (workflow.db)" -ForegroundColor Green
} else {
    Write-Host "📝 Seeding database with demo data..." -ForegroundColor Cyan
    .\venv\Scripts\python.exe seed_data.py
    Write-Host "✅ Database initialized" -ForegroundColor Green
}

# Start servers
cd ..
Write-Host ""
Write-Host "[4/4] Starting servers..." -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Backend starting on http://localhost:8000" -ForegroundColor Green
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "In a new terminal, run:" -ForegroundColor Cyan
Write-Host "   cd frontend && npm install && npm start" -ForegroundColor Cyan
Write-Host ""
Write-Host "🔑 Demo Login:" -ForegroundColor Cyan
Write-Host "   Email: faculty@psgai.edu.in" -ForegroundColor Cyan
Write-Host "   Password: Password@123" -ForegroundColor Cyan
Write-Host ""

cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
