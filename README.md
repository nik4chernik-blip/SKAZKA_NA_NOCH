# Бесплатная площадка сказок на GitHub Pages

Статический архив для ссылок из MAX. Сборка не использует LLM, vision или Teletype.

## Локальная сборка

```bash
python3 build_site.py \
  --source /root/.hermes/scripts/teletype_spool \
  --output site \
  --base-url https://OWNER.github.io/REPOSITORY
```

После появления настоящего URL генератор создаёт `site/articles.json` — его можно использовать как источник проверенных ссылок для MAX.

## Публикация

Репозиторий должен быть опубликован через GitHub Pages с GitHub Actions. Workflow находится в `.github/workflows/pages.yml`.

До загрузки в GitHub нужно заменить `OWNER` и `REPOSITORY` на фактические значения. Секреты и cookies в репозиторий не копируются.
