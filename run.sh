#!/bin/bash

echo "Запуск RecoFilm через Docker Compose..."
# -d запускает в открепленном режиме
# --build обеспечивает сборку образов, если произошли изменения в Dockerfile
# --force-recreate обеспечивает пересоздание контейнеров для применения изменений
docker-compose up -d --build --force-recreate

if [ $? -ne 0 ]; then
    echo "Ошибка: Не удалось запустить Docker Compose."
    exit 1
fi

echo "RecoFilm запущен. Откройте http://localhost:8000 в вашем браузере."
echo "Для просмотра логов: docker-compose logs -f"