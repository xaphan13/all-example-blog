# Логика и работа кода

## Жизненный цикл приложения

### Инициализация

1. **Импорт модулей**. При запуске uvicorn импортируется `../app/main.py`.
2. **Создание глобальных singleton**: `settings`, `pool`, `templates`, `_md`, `_hasher`, `_serializer`.
   - `ConnectionPool(..., open=False)` в `../app/database.py` не открывает соединения сразу.
3. **Регистрация компонентов**:
   - Lifespan-контекст `app/main.py::lifespan`.
   - Mount статики `/static` и `/media`.
   - Подключение роутеров `public` и `admin`.
   - Глобальный обработчик `StarletteHTTPException` для кастомной 404.

### Запуск

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    pool.open()      # открывает пул psycopg
    yield
    pool.close()     # graceful shutdown
```

После `yield` FastAPI начинает принимать запросы. Пул имеет `min_size=1, max_size=10`.

### Завершение работы

При получении сигнала завершения lifespan выходит из `yield` и вызывает `pool.close()`, закрывая соединения с PostgreSQL.

## Ключевые бизнес-процессы

### 1. Аутентификация администратора

```
GET /admin/login
  → если cookie валидна, редирект /admin
  → иначе шаблон login.html

POST /admin/login
  → app/queries/users.py::get_by_username(db, username)
  → app/auth.py::verify_password(password_hash, password) с argon2
  → app/auth.py::create_session_token(username)
  → set_cookie HttpOnly SameSite=Lax
  → Redirect 303 /admin
```

Проверка сессии в защищённых маршрутах выполняется через `Depends(require_admin)`, который возвращает 303 на `/admin/login` при отсутствии/невалидности cookie.

### 2. CRUD поста

**Создание** (`POST /admin/posts/new`):

1. Получение form-данных (`title`, `slug`, `summary`, `cover_image`, `content_md`, `published`, `tags`).
2. `slug = unique_slug(db, slug or title)` — генерация и дедупликация.
3. `render_markdown(content_md)` → `content_html`.
4. `posts.create(...)` — INSERT с `published_at = now()` только если `published=True`.
5. `_save_tags(db, post_id, tags_str)` — нормализация имён, `get_or_create`, удаление старых связей и вставка новых.
6. Редирект на `/admin`.

**Обновление** (`POST /admin/posts/{id}/edit`):

Аналогично созданию, но с `exclude_id=post_id` для `unique_slug` и `UPDATE posts SET ...`.

**Публикация/снятие с публикации** (`POST /admin/posts/{id}/publish`):

- `posts.set_published(db, post_id, not post["published"])`.
- `published_at` устанавливается только при первой публикации (CASE WHEN ... IS NULL).

**Удаление** (`POST /admin/posts/{id}/delete`):

- `posts.delete(db, post_id)` — `DELETE FROM posts WHERE id = %s`.
- Связанные записи в `post_tags` удаляются каскадно (`ON DELETE CASCADE`).

### 3. Full-text search

- Поисковый вектор `search_vector` генерируется автоматически PostgreSQL:
  - `title` — вес A;
  - `summary` — вес B;
  - `content_md` — вес C.
- Запрос `websearch_to_tsquery('english', %s)` поддерживает кавычки, `OR`, `-`.
- Результаты сортируются по `ts_rank` и `published_at DESC`.

### 4. Загрузка изображений

- Изображения принимаются через `UploadFile` в `POST /admin/api/images`.
- Проверяется расширение: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.svg`.
- Файл сохраняется как `media/<uuid>.<ext>`.
- Возвращается URL `/media/<uuid>.<ext>`.
- В редакторе изображения вставляются как markdown `![alt](url)`.

### 5. Очистка медиа

- `POST /admin/media/cleanup` вызывает `app/media_cleanup.py::delete_orphans(db)`.
- Собирает blob из `content_md` и `cover_image` всех постов.
- Для каждого файла в `../media` (старше 1 часа) проверяет, встречается ли `/media/<relative_path>` в blob.
- Удаляет неиспользуемые файлы и пустые подпапки.

## Роутинг и middleware

### Роутеры

| Роутер | Префикс | Файл |
|--------|---------|------|
| public | `/` | `../app/routers/public.py` |
| admin | `/admin` | `../app/routers/admin.py` |

### Публичные маршруты

- `GET /` — главная с пагинацией (`page` query).
- `GET /about` — страница о себе.
- `GET /post/{slug}` — страница поста.
- `GET /tags/{slug}` — посты по тегу.
- `GET /search?q=...` — поиск.
- `GET /robots.txt` — robots + sitemap URL.
- `GET /sitemap.xml` — XML sitemap.

### Административные маршруты

- `GET/POST /admin/login`, `POST /admin/logout`.
- `GET /admin` — список постов.
- `GET/POST /admin/posts/new` — создание.
- `GET/POST /admin/posts/{id}/edit` — редактирование.
- `POST /admin/posts/{id}/publish` — переключение публикации.
- `POST /admin/posts/{id}/delete` — удаление.
- `POST /admin/media/cleanup` — очистка изображений.
- `POST /admin/api/preview` — предпросмотр markdown.
- `POST /admin/api/images` — загрузка изображения.

### Middleware / обработка ошибок

- В `../app/main.py` зарегистрирован глобальный обработчик `StarletteHTTPException`.
- Если `status_code == 404`, рендерится `../app/templates/404.html`.
- Все остальные HTTP-исключения делегируются стандартному FastAPI-обработчику (JSON).
- Нет кастомных middleware для логирования, CORS, rate limiting, request ID.

## Обработка ошибок и логирование

### Обработка ошибок

- **404**: кастомный HTML-шаблон.
- **401/403**: в login-форме возвращается HTML-страница с сообщением об ошибке; для защищённых маршрутов — 303 редирект.
- **400**: при неподдерживаемом типе изображения.
- **500**: стандартный FastJSON-ответ; нет кастомного обработчика.

### Логирование

- В коде нет явных вызовов `logging`.
- Логи uvicorn/ASGI выводятся в stdout/stderr благодаря `PYTHONUNBUFFERED=1` в `../Dockerfile`.
- Backup-скрипт пишет в `backups/backup.log` (если cron настроен с редиректом).

### Замечания по надёжности

- `POST /admin/posts/{id}/delete` не проверяет существование поста перед удалением; SQL не вернёт ошибки, но UX неинформативен.
- `posts.delete` не возвращает результат; нет обратной связи, если id не существовал.
- Загрузка файлов не ограничивает размер, что потенциально позволяет заполнить диск.
- Нет CSRF-токенов в формах админки (защита только SameSite=Lax).
