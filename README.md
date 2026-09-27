UNI DOWNLOAD 1.0

Скачивание видео (и аудио) с YouTube и других сайтов, поддерживаемых [yt-dlp](https://github.com/yt-dlp/yt-dlp). Простой GUI на Python/tkinter, можно вставить сразу несколько ссылок (по одной на строку) и скачать их все подряд.

## Запуск из исходников

```bash
pip install -r requirements.txt
python main.py
```

Для скачивания только звука (MP3) или для склейки видео+аудио в лучшем качестве нужен `ffmpeg` в PATH.

## Сборка .exe для Windows

В этом репозитории есть GitHub Actions workflow `.github/workflows/build-windows-exe.yml`, который собирает `UniDownload.exe` на `windows-latest` через PyInstaller.

1. Запушьте изменения в `main.py`/`requirements.txt` (или запустите workflow вручную во вкладке **Actions → Build Windows EXE → Run workflow**).
2. После завершения сборки скачайте готовый `.exe` из артефактов запуска (**Actions → выбранный run → Artifacts → UniDownload-exe**).

### Локальная сборка на Windows

```powershell
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --name UniDownload main.py
```

Готовый файл появится в `dist/UniDownload.exe`. Для поддержки MP3/склейки форматов положите `ffmpeg.exe` рядом с итоговым `.exe`.
