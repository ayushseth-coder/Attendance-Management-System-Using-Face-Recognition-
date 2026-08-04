import os
# --- RAM OPTIMIZATION FOR CLOUD HOSTING (512MB RAM LIMIT) ---
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['TF_NUM_INTRAOP_THREADS'] = '1'
os.environ['TF_NUM_INTEROP_THREADS'] = '1'
os.environ['MALLOC_TRIM_THRESHOLD_'] = '65536'
# -------------------------------------------------------------

from main import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
