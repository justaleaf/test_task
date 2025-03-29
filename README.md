# Тестовое задание для компании PAVEPO

## Формулировка задания
```
Реализовать сервис по загрузке аудио-файлов от пользователей, используя FastAPI, SQLAlchemy и Docker. Пользователи могут давать файлам имя в самом API.
Авторизацию пользователей реализовать через Яндекс.
Файлы хранить локально, хранилище использовать не нужно.
Использовать асинхронный код.
БД - PostgreSQL 16.
```

## Ожидаемый результат
1. Готовое API с возможностью авторизации через Яндекс с последующей аутентификацией к запросам через внутренние токены API.
Доступные эндпоинты: авторизация через яндекс, обновление внутреннего access_token; получение, изменение данных пользователя, удаление пользователя от имени суперпользователя; получение информации о аудио файлах пользователя: название файлов и путь в локальной хранилище.
2. Документация по развертыванию сервиса и БД в Docker.

## Запуск сервиса
Для запуска сервиса требуется:
1. Установить Docker
2. Создать файл .env с переменными окружения (секретки Яндекса и строка подключения к БД)
3. Запустить команду
    ```
    docker compose up -d
    ```
4. Перейти по ссылке http://localhost:8000/docs