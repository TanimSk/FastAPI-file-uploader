payload:
```
curl -X 'POST' \
  'http://127.0.0.1:8000/upload/?compression_level=50&path="file-path"' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'file=@video.mp4'
```
