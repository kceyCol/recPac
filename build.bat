@echo off
echo Building frontend...
cd frontend
npm install
npm run build
cd ..
echo Frontend build complete!
echo Starting Flask server...
python app.py
pause