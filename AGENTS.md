# AGENTS.md -- gg-test

Instructions for AI coding agents (Codex, Claude, etc.).

## Stack
- Primary: Python
- Frameworks: Flask
- Package manager: pip

## Commands
- **install**: `pip install -e .[dev]`
- **test**: `pytest`

## Structure
- `static/` (static)
- `tests/` (tests)
- `uploads/`

## Semantic Code Search (grepai)

This project has grepai configured for semantic code search.
Use it BEFORE reading files to find relevant code efficiently.

### Search by meaning
```
grepai search "authentication logic"     # finds handleUserSession, etc.
grepai search "database connection pool"  # finds pool setup even if named differently
grepai search "error handling pattern"    # finds try/catch conventions
```

### Trace call graphs (before changing a function)
```
grepai trace callers "functionName"   # who calls this function?
grepai trace callees "functionName"   # what does this function call?
```

### When to use grepai vs grep
- **grepai**: when you know WHAT you're looking for conceptually but not the exact name
- **grep/ripgrep**: when you know the exact string, variable name, or pattern

### Rules
- Always run `grepai search` before modifying unfamiliar code areas
- Use `grepai trace callers` before refactoring any public function
- Prefer grepai over reading entire files to save tokens

## Project Rules

# Project Constitution

## 1. Сначала сохраняй контракт проекта

Проект сейчас фактически **FastAPI + SQLite**, хотя в описании указан Flask. Не смешивай фреймворки без явной миграции. Любое изменение API должно сохранять ожидаемые эндпоинты, форматы JSON, статусы ошибок и поведение фронтенда.

## 2. Безопасность важнее удобного хака

Нельзя добавлять `eval`, SQL через f-string, небезопасный `innerHTML`, логирование паролей, токенов и секретов. Любой пользовательский ввод считается недоверенным: параметры SQL, HTML, имена файлов, поисковые строки, URL и загружаемые файлы должны валидироваться или экранироваться.

## 3. Аутентификация не должна быть имитацией

Пароль не может быть токеном. Токены должны быть отдельными, случайными, отзываемыми или хотя бы безопасно подписанными. Пароли должны храниться только в виде хеша. Любая ручка, работающая с заметками, файлами или пользователями, обязана явно проверять владельца ресурса.

## 4. Данные изолированы по пользователям

Заметки, поиск, редактирование, удаление и загрузки не должны раскрывать данные другого пользователя. Публичность заметки должна быть осознанным исключением, а не обходом авторизации. Любой новый запрос к БД проверяется на утечки между пользователями.

## 5. Конфигурация живёт вне кода

Секреты, `DEBUG`, пароли администратора, база данных, CORS и пути загрузок должны приходить из окружения или конфигурационного слоя. В коде не должно быть production-секретов, тестовых паролей и отладочных эндпоинтов, раскрывающих конфиг.

## 6. Тесты фиксируют поведение перед изменениями

Перед рефакторингом или исправлением уязвимости сначала добавляй тест, который показывает текущее или желаемое поведение. Минимальный набор: регистрация, логин, CRUD заметок, запрет доступа к чужим заметкам, поиск, загрузка файлов, ошибки авторизации.

## 7. Маленькие изменения, проверяемый результат

Не добавляй зависимости и абстракции без необходимости. Меняй минимальный участок кода, запускай релевантные тесты, проверяй API вручную там, где тестов мало. Финальное состояние должно быть понятным: что изменилось, чем проверено, какие риски остались.


## References
- Specs: `openspec/specs/`
- Knowledge: `.gg/knowledge/`
- Constitution: `.gg/constitution.md`
