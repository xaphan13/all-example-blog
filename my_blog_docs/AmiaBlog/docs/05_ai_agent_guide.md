# AmiaBlog: контекст для AI-агентов

## Быстрый ориентир

- Точка входа динамического сервера: `main.py`.
- Точка входа статической генерации: `staticify.py`.
- Вся доменная логика: `core/`.
- Конфигурация: `config.json`, валидируется в `core/models.py`.
- Контент: `data/posts/*.md` + `data/attachments/`.
- Шаблоны: `templates/`; базовый — `templates/base.html`.

## Что нужно помнить при изменениях

1. **Глобальное состояние на уровне модуля.** `main.py` создает `config`, `posts_manager`, `renderer` и др. при импорте. Если вы меняете сигнатуру конструктора менеджера, обновите и `main.py`, и `staticify.py`.

2. **Два режима рендеринга.** `TemplateRenderer` используется как для HTTP-ответов (`render()`), так и для записи на диск (`render_static()` / `render_to_plain_text()`). Флаг `is_static` в `static_params` управляет URL в шаблонах.

3. **Markdown рендерится в браузере.** Сервер хранит сырой Markdown; HTML получается через `markdown-it` на клиенте. Если вы добавляете плагины Markdown, подключайте их в `templates/post.html` и/или `static/`.

4. **Поиск в памяти.** `PostsManager` использует `sqlite3.connect(":memory:")`. Для live-сервера индекс строится; для статики — `build_search_index=False`.

5. **Watchdog и live-preview.** `PostsManager` автоматически запускает наблюдение за `data/posts/`. `LivePreviewManager` мутирует `posts_manager._post_reload_hook`. В production live-preview должен быть выключен.

6. **Подсветка синтаксиса.** Языки берутся из `config.json`; недостающие `.min.js` скачиваются в `static/hljs_11.1.1/` при старте. Не добавляйте сюда секреты или неизвестные языки без проверки CDN.

7. **I18n.** Переводы — JSON в `languages/`. Шаблоны обращаются через `i18n.<key>`. Если строка содержит 2+ placeholder-а, используйте именованные placeholder-ы (`{n_posts}`), чтобы порядок слов можно было менять в разных языках.

8. **URL-кодирование тегов.** В шаблонах используется фильтр `urlencode`: `/tag/{{ tag | urlencode }}`.

9. **Валидация и CI.** Перед коммитом запускайте:
   ```bash
   uv run black --check .
   uv run pyright
   ```
   CI: `.github/workflows/black-check.yml`, `.github/workflows/pyright-check.yml`.

10. **Статическая генерация.** Добавляя новую страницу, добавьте маршрут в `main.py`, шаблон в `templates/` и, если нужен статический вывод, шаг рендеринга в `staticify.py`.

## Распространенные задачи

| Задача | Файлы |
|---|---|
| Новый маршрут | `main.py` → `templates/<page>.html` → `staticify.py` (опционально) |
| Изменить поиск | `core/posts.py` (`search`, `_build_search_index`) и `config.json` (`search_method`) |
| Новый язык UI | `languages/<code>.json` + `config.json` (`site_language`) |
| Новое поле в конфиге | `core/models.py` + `config.json` + шаблоны |
| Изменить верстку | `templates/base.html` и/или наследующие шаблоны |
| Поддержать новый Markdown-плагин | `templates/post.html`, `static/` |
