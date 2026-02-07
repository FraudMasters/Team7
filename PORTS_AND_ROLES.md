# AgentHR - Изменения портов и настройка ролей

## Обзор изменений

Изменены порты всех сервисов на диапазон **5xxx** для избежания конфликтов со стандартными портами на macOS.
Настроена система ролей с тремя уровнями доступа: `admin`, `recruiter`, `job_seer`.

## Новые порты

### Основные сервисы (docker-compose.yml)

| Сервис | Старый порт | Новый порт | Внутренний порт |
|--------|------------|------------|----------------|
| PostgreSQL | 5432 | **55432** | 5432 |
| Redis | 6379 | **56379** | 6379 |
| cAdvisor | 8080 | **5800** | 8080 |
| Frontend | 3000 | **5300** | 5173 |
| Grafana | 3001 | **5301** | 3000 |
| Prometheus Exporter | 9187 | 9187 | 9187 |
| Celery Exporter | 9540 | 9540 | 9540 |

### Микросервисы (docker-compose.microservices.yml)

| Сервис | Старый порт | Новый порт | Внутренний порт |
|--------|------------|------------|----------------|
| Kong Proxy | 8888 | **5888** | 8000 |
| Kong Admin API | 8001 | **5801** | 8001 |
| Keycloak | 8081 | **5881** | 8080 |
| Loki | 3100 | **5310** | 3100 |
| Promtail | 9080 | **5900** | 9080 |
| Consul UI | 8500 | 8500 | 8500 |
| Jaeger UI | 16686 | 16686 | 16686 |

### Фронтенд (разработка)

| Ресурс | Порт |
|--------|------|
| Vite dev server | 5173 или 5174 (авто) |

## Пользователи и роли

### Роли в Keycloak

| Роль | Описание | Доступ |
|------|----------|--------|
| `admin` | Администратор | Полный доступ ко всем функциям |
| `recruiter` | Рекрутер | Доступ к дашборду рекрутера, кандидатам, вакансиям |
| `job_seeker` | Соискатель | Доступ к поиску вакансий, резюме, application flow |

### Тестовые пользователи

| Роль | Логин | Пароль | Редирект после входа |
|------|-------|--------|------------------------|
| **Administrator** | `agenthr_admin` | `admin123` | `/recruiter/dashboard` |
| **Recruiter** | `recruiter` | `recruiter123` | `/recruiter/dashboard` |
| **Job Seeker** | `testuser` | `test123` | `/jobs` |

## Файлы изменённые для ролей

### Frontend

1. **`src/auth/oidcConfig.ts`**
   - Добавлен `roles` в `scope`

2. **`src/auth/CallbackPage.tsx`**
   - Редирект на основе роли после авторизации
   - `admin` → `/recruiter/dashboard`
   - `recruiter` → `/recruiter/dashboard`
   - `job_seeker` → `/jobs`

3. **`src/pages/LandingPage.tsx`**
   - Авторизованные пользователи редиректятся сразу на нужную страницу

4. **`src/hooks/useRoles.ts`** (новый файл)
   - Хуки для работы с ролями:
     - `useUserRoles()` - получить роли пользователя
     - `useHasRole(role)` - проверить наличие роли
     - `useIsAdmin()`, `useIsRecruiter()`, `useIsJobSeeker()`

5. **`src/hooks/index.ts`**
   - Экспорт всех хуков ролей

## Переменные окружения

### Фронтенд (.env)

```bash
VITE_API_URL=http://localhost:5888
VITE_OIDC_AUTHORITY=http://localhost:5881/realms/agenthr
VITE_OIDC_CLIENT_ID=agenthr-frontend
```

### Изменения при деплое

При деплое на продакшн необходимо обновить:
1. Порт Kong API Gateway в `.env` фронтенда
2. Порт Keycloak OIDC Authority
3. Все внутренние подключения сервисов к БД и Redis (они используют внутренние порты Docker-сети, так что это не критично)

## Как применить изменения

### Вариант 1: Перезапустить контейнеры

```bash
# Остановить контейнеры
docker-compose -f docker-compose.yml -f docker-compose.microservices.yml down

# Запустить с новыми портами
docker-compose -f docker-compose.yml -f docker-compose.microservices.yml up -d
```

### Вариант 2: Полный пересбор и запуск

```bash
# Пересобрать фронтенд
cd frontend
npm install
npm run build

# Перезапустить все контейнеры
docker-compose -f docker-compose.yml -f docker-compose.microservices.yml down
docker-compose -f docker-compose.yml -f docker-compose.microservices.yml up -d --build
```

## Проверка работоспособности

После запуска проверьте:

```bash
# Kong API Gateway
curl http://localhost:5888/api/candidates/

# Keycloak
curl http://localhost:5881/realms/agenthr

# Frontend (Docker)
curl http://localhost:5300

# Frontend (dev)
npm run dev  # запустится на 5173 или 5174
```

## Git коммит

Для сохранения изменений в git:

```bash
git add docker-compose.yml docker-compose.microservices.yml frontend/.env frontend/src/
git commit -m "refactor: change ports to 5xxx range and implement role-based access control

- Change PostgreSQL port: 5432 → 55432
- Change Redis port: 6379 → 56379
- Change Keycloak port: 8081 → 5881
- Change Kong port: 8888 → 5888
- Change frontend port: 3000 → 5300
- Add role-based redirects after login
- Add admin, recruiter, job_seeker roles
- Create useRoles hook for role management
"
```

## Краткая инструкция для разработки

1. **Запуск всех сервисов:**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.microservices.yml up -d
   ```

2. **Фронтенд (разработка):**
   ```bash
   cd frontend
   npm run dev
   # Откроется http://localhost:5173 (или 5174 если занят)
   ```

3. **Фронтенд (Docker):**
   ```bash
   # Автоматически стартует с docker-compose
   http://localhost:5300
   ```

4. **API Gateway:**
   ```bash
   http://localhost:5888
   ```

5. **Keycloak Admin:**
   ```bash
   # Консоль: http://localhost:5881/admin
   # realm: agenthr
   # admin/admin
   ```

## Solving Port Conflicts

Если порт всё равно занят:

1. Найдите процесс:
   ```bash
   lsof -i :5432  # или другой порт
   ```

2. Остановите или измените порт в `docker-compose.yml`:
   ```yaml
   ports:
     - "55433:5432"  # Изменить только хост-порт
   ```

3. Или используйте случайный порт:
   ```yaml
   ports:
     - "0:5432"  # Docker сам выберет свободный порт
   ```
