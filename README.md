payload:
```
curl -X 'POST' \
  'http://127.0.0.1:8000/upload/?compression_level=50&path="file-path"' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@video.mp4'
```


Service file:
```
[Unit]
Description=FastAPI File Uploader
After=network.target

[Service]
User=<username>
Group=www-data
Type=simple
WorkingDirectory=/home/<username>/FastAPI-file-uploader
ExecStart=/home/<username>/FastAPI-file-uploader/venv/bin/python -m gunicorn \
--workers 2 \
--bind 0.0.0.0:8141 \
--access-logfile /var/log/gunicorn/fastapi-file-server-access.log \
--error-logfile /var/log/gunicorn/fastapi-file-server-error.log \
--worker-class uvicorn.workers.UvicornWorker \
app:app

[Install]
WantedBy=multi-user.target
```
