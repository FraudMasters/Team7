# API Gateway Configuration
# Конфигурация API Gateway

Этот каталог содержит конфигурации для двух популярных API Gateway решений:
**Kong** (выбран по умолчанию) и **Traefik** (альтернативный вариант).

---

## Kong Gateway (Выбран по умолчанию)

### Преимущества Kong
- ✅ Мощная система плагинов для аутентификации, rate limiting, CORS
- ✅ Поддержка декларативной конфигурации (используется в этом проекте)
- ✅ Отличная производительность на высоких нагрузках
- ✅ Административная панель (http://localhost:8002)
- ✅ OpenID Connect и JWT плагины для интеграции с Keycloak

### Использование Kong

Конфигурация по умолчанию в `docker-compose.microservices.yml` использует Kong:

```bash
# Запуск с Kong (по умолчанию)
docker-compose -f docker-compose.microservices.yml up -d api_gateway

# Проверка здоровья
curl -s http://localhost:8888/health

# Доступ к Admin API
curl http://localhost:8001

# Доступ к Admin GUI (Dashboard)
open http://localhost:8002
```

### Конфигурационные файлы Kong
- `kong.yml` - Декларативная конфигурация (сервисы, маршруты, плагины)

### Порты Kong
- `8888` - Прокси порт (основной API)
- `8443` - Прокси порт SSL
- `8001` - Admin API
- `8002` - Admin GUI (Dashboard)

---

## Traefik (Альтернатива)

### Преимущества Traefik
- ✅ Автоматическое обнаружение сервисов (Docker, Consul, Kubernetes)
- ✅ Нативная поддержка LetsEncrypt для автоматического SSL
- ✅ Встроенный Dashboard с метриками
- ✅ Проще в настройке для development environments
- ✅ Отличная интеграция с Docker Compose

### Использование Traefik

Для переключения на Traefik, отредактируйте `docker-compose.microservices.yml`:

```yaml
# Замените сервис api_gateway на:
api_gateway:
  image: traefik:v3.0
  container_name: api_gateway
  command:
    - "--api.dashboard=true"
    - "--providers.docker=true"
    - "--providers.file.filename=/etc/traefik/dynamic/traefik.yml"
    - "--entrypoints.web.address=:8888"
    - "--entrypoints.websecure.address=:8443"
  ports:
    - "8888:8888"   # Web entrypoint
    - "8443:8443"   # Websecure entrypoint
    - "8080:8080"   # Dashboard (без аутентификации для dev)
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock:ro
    - ./infrastructure/api-gateway/traefik.yml:/etc/traefik/dynamic/traefik.yml:ro
```

### Конфигурационные файлы Traefik
- `traefik.yml` - Динамическая конфигурация (маршруты, сервисы, middleware)

### Порты Traefik
- `8888` - Web entrypoint (основной API)
- `8443` - Websecure entrypoint (SSL)
- `8080` - Dashboard

---

## Сравнение характеристик

| Характеристика | Kong | Traefik |
|----------------|------|---------|
| **Производительность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Простота настройки** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Plugin ecosystem** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Auto-discovery** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Admin UI** | ✅ | ✅ |
| **JWT Auth** | ✅ | ✅ (через middleware) |
| **Rate Limiting** | ✅ (с Redis) | ✅ |
| **Documentation** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## Выбор API Gateway

### Рекомендация: Используйте Kong для production

**Причины:**
1. Более зрелая экосистема плагинов для enterprise-функций
2. Лучшая производительность на высоких нагрузках
3. Гибкость JWT плагина для интеграции с Keycloak
4. Enterprise-поддержка от Kong Inc.

### Используйте Traefik для development

**Причины:**
1. Быстрее настроить для локальной разработки
2. Автоматическое обнаружение Docker контейнеров
3. Отличный Dashboard для отладки
4. Меньше конфигурационных файлов

---

## Следующие шаги

После запуска API Gateway:

1. **Проверка здоровья:**
   ```bash
   curl -s http://localhost:8888/health | grep -q 'healthy' && echo 'API Gateway healthy'
   ```

2. **Тестирование маршрутов:**
   ```bash
   # Пример: Обращение к сервису резюме через Gateway
   curl http://localhost:8888/api/resumes
   ```

3. **Настройка аутентификации (Phase 8):**
   - Интеграция с Keycloak
   - JWT плагин конфигурация
   - OAuth2/OIDC настройки

---

## Troubleshooting

### Kong не запускается
```bash
# Проверка логов
docker logs api_gateway

# Проверка конфигурации
docker exec api_gateway kong validate /usr/local/kong/declarative/kong.yml
```

### Traefik не обнаруживает сервисы
```bash
# Убедитесь, что Docker socket доступен
docker exec api_gateway ls /var/run/docker.sock

# Проверьте логи Traefik
docker logs api_gateway
```

### Ошибки CORS
- Проверьте настройки origins в конфигурационных файлах
- Убедитесь, что фронтенд отправляет правильные заголовки

---

## Дополнительные ресурсы

- [Kong Documentation](https://docs.konghq.com/)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [Kong vs Traefik Comparison](https://www.konghq.com/kong-vs-traefik)
