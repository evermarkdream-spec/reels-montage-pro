# Инструменты, версии и расширения

## Обязательная основа

| Инструмент | Задача | В комплекте |
|---|---|---|
| Remotion и @remotion/media 4.0.538 | Редактируемые видео/аудио/слои, композиция, Studio, рендер | package.json + lock-файл |
| React 19.2.3, TypeScript 5.9.3 | Предметная графика и анимация по кадрам | Зависимости проекта |
| @remotion/captions 4.0.538 | Формат caption-данных | Зависимость проекта |
| faster-whisper 1.2.1 | Локальная русская транскрипция с таймингами | requirements.txt, модель скачивается при первом использовании |
| OpenCV | Ориентация и кадрирование по лицу, контроль кадров | Python-зависимость |
| FFmpeg/FFprobe | Метаданные, нарезка, аудио, ducking, проверка экспорта | Нужны в PATH, бинарники не распространяются |
| Lucide React | Иконки действий | npm dependency (версия зафиксирована lock-файлом) |
| Onest, Unbounded, Inter | Субтитры, заголовки, вспомогательные компоненты | Локальные файлы + OFL |
| Prettier | Раздельные редактируемые JSX-узлы | Dev dependency |

Remotion имеет собственные условия использования; MIT исходного шаблона их не заменяет. [Официальная лицензия](https://www.remotion.dev/docs/license/pricing).

## Опционально

ImageGen или другой генератор изображений — для контекстных предметов и вырезок, когда они нужны сцене. Использовать реально доступный инструмент агента. Текст сцены/субтитры оставлять редактируемыми, не запекать в картинку. Подписка и внешние API-ключи не включены.

Fluent Emoji (Microsoft/MIT): в проекте есть несколько открытых предметных PNG; scripts/get-emoji.py может загрузить дополнительные по именам. Apple Emoji и Tahoma в комплект не включены. Точные логотипы продукта брать из официального источника для конкретной сцены, а не генерировать похожий знак.

CLAP + Hybrid Demucs — дополнительный локальный анализ характера звука и приблизительное разделение музыки/речи. Для обычного монтажа и ducking не требуются. Если студент просит анализ референсов:

```bash
python -m venv .venv-audio
.venv-audio/bin/python -m pip install -r requirements-audio.txt
.venv-audio/bin/python scripts/setup-audio-analysis.py
.venv-audio/bin/python scripts/analyze-music.py reference.mp4 --out out/audio-analysis --separate --windows 3
```

На Windows интерпретатор .venv-audio\\Scripts\\python.exe. Загрузка весов занимает дополнительное место и требует совместимости PyTorch с системой. Модельные оценки не являются распознаванием названия песни, точной тональности или человеческим прослушиванием. Музыку из чужого ролика в монтаж не переносить.

## Источники и происхождение

- Основа кода: https://github.com/alexandersadekov/video-montage-template — MIT; LICENSE сохранён.
- Документация Remotion: https://www.remotion.dev/docs/.
- faster-whisper: https://github.com/SYSTRAN/faster-whisper.
- Fluent: https://github.com/microsoft/fluentui-emoji.
- Шрифты: Google Fonts Onest / Unbounded, лицензии OFL рядом с файлами.
- Музыка: The Child — Umplix, https://opengameart.org/content/the-child, CC0. Трек входит как разрешённый стартовый вариант; оформление по нему можно заменить.

Источники Remotion, faster-whisper и лицензия музыки проверены 03.11.2026. Точная сборка проекта определяется lock-файлом, а не «latest».
