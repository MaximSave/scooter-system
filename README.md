# Scooter System

Демонстрационная событийная система для мониторинга парка электросамокатов в Москве. Приложение моделирует аренды и перемещения самокатов по дорожному графу, передаёт события через Kafka, сохраняет состояние в PostgreSQL/PostGIS и предоставляет наблюдаемость через Prometheus, Loki и Grafana.

## Возможности

- симуляция 100 самокатов: начало и завершение аренды, координаты, заряд и постановка на зарядку;
- построение маршрутов по графу городских дорог и выбор популярных точек назначения с весами;
- потоковая передача событий в Kafka (`scooter_events`);
- хранение истории событий, актуального состояния и треков в PostgreSQL с PostGIS;
- метрики генератора и consumer в Prometheus;
- централизованный сбор контейнерных логов в Loki через Vector и визуализация в Grafana;
- запуск всего стенда одной командой Docker Compose.

## Архитектура

```text
Граф Москвы + точки притяжения
                │
                ▼
      generator (Python)
       ├── PostgreSQL/PostGIS: events, scooters
       └── Kafka: scooter_events
                    │
                    ▼
          consumer (Python)
       ├── PostgreSQL/PostGIS: scooter_state, scooter_route
       └── /metrics ──► Prometheus ──► Grafana

Docker logs ──► Vector ──► Loki ──► Grafana
```

## Стек

Python 3.11, Apache Kafka и ZooKeeper, PostgreSQL 15 + PostGIS 3.4, Docker Compose, Prometheus, Grafana, Loki, Vector, NetworkX.

## Быстрый старт

### Требования

- Docker Desktop с включённым Docker Compose;
- Git; Git LFS нужен, если файл дорожного графа хранится в репозитории через LFS;
- свободные порты `3000`, `3100`, `5432`, `8000`, `9090` и `9092`.

### Запуск

```bash
git lfs install
git clone https://github.com/MaximSave/scooter-system.git
cd scooter-system
git lfs pull  # выполните, если moscow_graph.pkl хранится в Git LFS
docker compose up --build -d
docker compose ps
```

Перед запуском убедитесь, что существует файл `generator/city/moscow_graph.pkl`. Если его нет, сформируйте граф, выполнив ячейки ноутбука `generator/city/Untitled.ipynb` (он использует OSMnx), либо добавьте подготовленный файл в эту папку.

При первом старте Docker скачает образы и создаст базу данных. Проверить поток событий можно командой:

```bash
docker compose logs -f generator consumer
```

Остановить стенд:

```bash
docker compose down
```

Чтобы удалить также данные PostgreSQL, Loki и Grafana, используйте `docker compose down -v`.

## Сервисы

| Сервис | Адрес | Назначение |
| --- | --- | --- |
| Grafana | [http://localhost:3000](http://localhost:3000) | Дашборды и просмотр логов; анонимный вход включён |
| Prometheus | [http://localhost:9090](http://localhost:9090) | Метрики generator и consumer |
| Consumer metrics | [http://localhost:8000/metrics](http://localhost:8000/metrics) | Метрики обработчика событий |
| Loki | [http://localhost:3100](http://localhost:3100) | Хранилище логов |
| PostgreSQL/PostGIS | `localhost:5432` | БД `scooters`, пользователь и пароль `scooter` |
| Kafka | `localhost:9092` | Топик `scooter_events` внутри Docker-сети |

## Данные и события

При инициализации создаются 100 самокатов. Генератор публикует события:

| Тип | Описание |
| --- | --- |
| `rental_start` | самокат взят в аренду |
| `location_update` | новая позиция и уровень заряда во время поездки |
| `rental_end` | аренда завершена |
| `charging_start` | разряженный самокат отправлен на зарядку |

В PostgreSQL хранятся:

- `scooters` — текущее состояние парка;
- `events` — журнал всех сгенерированных событий;
- `scooter_state` — последняя известная позиция каждого самоката;
- `scooter_route` — история точек маршрутов.

## Наблюдаемость

Prometheus опрашивает `/metrics` обоих Python-сервисов каждые 5 секунд. Основные метрики:

- `events_generated_total` — количество событий, созданных генератором;
- `scooter_events_total` — количество событий, обработанных consumer;
- `scooter_battery` — текущий заряд самоката;
- `scooter_last_seen_timestamp` — время последнего события самоката.

Vector считывает логи Docker-контейнеров и отправляет их в Loki. В Grafana добавьте источники данных `Prometheus` (`http://prometheus:9090`) и `Loki` (`http://loki:3100`), затем создайте панели для метрик и логов.

## Скриншоты

<p align="center">
  <img src="images_/Снимок экрана 2026-01-24 202515.png" alt="Дашборд Grafana" width="48%">
  <img src="images_/Снимок экрана 2026-01-24 202914.png" alt="Дашборд Grafana: метрики" width="48%">
</p>
<p align="center">
  <img src="images_/Снимок экрана 2026-01-24 202937.png" alt="Метрики Prometheus" width="48%">
  <img src="images_/Снимок экрана 2026-01-24 203238.png" alt="Карта самокатов" width="48%">
</p>

## Структура проекта

```text
generator/       Генератор событий и маршрутов
consumer/        Kafka-consumer, запись актуального состояния и метрики
db/              SQL-инициализация PostgreSQL/PostGIS
configs/         Конфигурации Prometheus, Loki и Vector
images_/         Скриншоты интерфейса и мониторинга
docker-compose.yml
```

## Важные замечания

- Файл `generator/city/moscow_graph.pkl` необходим генератору для запуска. В текущей поставке он отсутствует; его можно сформировать из `generator/city/Untitled.ipynb`. Если вы добавите граф в репозиторий, для большого файла используйте Git LFS (`git lfs track "generator/city/moscow_graph.pkl"`).
- Пароли в `docker-compose.yml` предназначены только для локального демонстрационного стенда. Для развёртывания в общей среде перенесите их в переменные окружения или менеджер секретов.
- Том `postgres_data` сохраняет данные между перезапусками. Чтобы повторно выполнить `db/init.sql`, остановите проект с удалением томов и запустите его заново.
