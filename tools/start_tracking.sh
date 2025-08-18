
pkill -f "0.0.0.0:15000"
nohup /usr/lib/python3.9/bin/mlflow ui --host 0.0.0.0 --port 15000 --backend-store-uri sqlite:///mydb.sqlite &