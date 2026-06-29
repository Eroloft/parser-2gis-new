<p align="center">
  <a href="#%E2%84%B9%EF%B8%8F-%D0%BE%D0%BF%D0%B8%D1%81%D0%B0%D0%BD%D0%B8%D0%B5">
    <img alt="Logo" width="128" src="https://user-images.githubusercontent.com/20641837/174094285-6e32eb04-7feb-4a60-bddf-5a0fde5dba4d.png"/>
  </a>
</p>
<h1 align="center">Parser2GIS</h1>

<p align="center">
  <a href="https://github.com/Eroloft/parser-2gis-new/actions/workflows/tests.yml"><img src="https://github.com/Eroloft/parser-2gis-new/actions/workflows/tests.yml/badge.svg" alt="Tests"/></a>
  <img src="https://img.shields.io/badge/python-3.8%20%E2%80%93%203.13-blue" alt="Поддерживаемые версии Python"/>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-LGPLv3-green" alt="Лицензия: LGPLv3"/></a>
  <a href="https://github.com/interlark/parser-2gis"><img src="https://img.shields.io/badge/fork%20of-interlark%2Fparser--2gis-orange" alt="Форк interlark/parser-2gis"/></a>
</p>

> ### 🍴 Это форк
> Проект является форком [**parser-2gis**](https://github.com/interlark/parser-2gis)
> (© Andy Trofimov, лицензия LGPLv3). Оригинальная разработка принадлежит автору;
> здесь добавлены модификации — см. раздел [«Изменения форка»](#-изменения-форка)
> и [CHANGELOG](CHANGELOG.md). Это независимый форк, не одобрен и не поддерживается
> оригинальным автором.

**Parser2GIS** - парсер сайта [2GIS](https://2gis.ru/) с помощью браузера [Google Chrome](https://google.com/chrome).

<img alt="Скриншот веб-дашборда Parser2GIS" src="docs/screenshot.png"/>

## ℹ️ Описание

Парсер для автоматического сбора базы адресов и контактов предприятий, которые работают на территории
России <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511175-3d47f0f0-4e3f-45d2-8495-95d0612a8a8c.svg"/>, Казахстана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511625-20420aef-59c3-426d-a112-654d2caf0dda.svg"/>, Беларуси <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511940-ce088ad1-d97f-4fa1-849a-9b887ad481c5.svg"/>,
Азербайджана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512176-1f6795a1-ceac-4865-a29f-b5720ce5115e.svg"/>, Киргизии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512234-286ca403-5194-4a6d-a59e-59201140078a.svg"/>, Узбекистана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512333-7ec1f36d-07fe-450d-b6f1-eed59a3b69c8.svg"/>, Чехии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512458-5a5d9531-a8f0-4624-99da-7069cde84926.svg"/>, Египта <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512581-71fa2106-8cc1-43cc-a680-b3ff420acb8a.svg"/>, Италии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512763-0b438e5b-3ff0-4717-a826-0baac9207167.svg"/>, Саудовской Аравии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512980-427a985a-df1b-42c8-90bb-2c61692b6654.svg"/>, Кипра <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513128-4367d2b1-feb9-4efe-bc57-73a15d178ef2.svg"/>, Объединенных Арабских Эмиратов <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513374-9afef8c7-923e-4a18-9cd8-c69645b99377.svg"/>, Чили <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513576-7209ce90-a04a-4258-9832-ef210198c3c4.svg"/>, Катара <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513757-143ee2bf-b66c-4766-bbe1-db896a33eac1.svg"/>, Омана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513865-27509b74-b08f-4d92-b83b-a0d3aaabe155.svg"/>, Бахрейна <img width="18px" src="https://user-images.githubusercontent.com/20641837/183514076-3b6c9496-7c95-4452-8ee1-8723d98f876d.svg"/>, Кувейта <img width="18px" src="https://user-images.githubusercontent.com/20641837/183514240-7eff8632-5cd2-46ac-bed4-e483bb2df5f0.svg"/>.

## ✨ Особенности
- 💰 Абсолютно бесплатный
- 🤖 Успешно обходит анти-бот блокировки на территории РФ
- 🖥️ Работает под Windows, Linux и MacOS
- 📄 Четыре выходных формата: CSV таблица, XLSX таблица, JSON список и **HTML-страница**
- 🌐 **Современный веб-интерфейс** в браузере — единственный UI (запуск без аргументов)
- 🔗 **Генератор ссылок** прямо в вебе: город + рубрика → готовый URL 2GIS
- 🧹 **Фильтры результатов:** без франшиз (1 филиал на организацию), только с телефоном / WhatsApp / соцсетями / e-mail / сайтом, по рейтингу и отзывам
- 💬 **HTML-страница с кнопками WhatsApp и 2GIS** — открыл и сразу пишешь клиентам
- ✨ **Чистый вид** вывода — только нужные колонки, без мусора
- ⚙️ Расширенные настройки (лимит RAM, задержка кликов, кодировка, CSV-опции) в той же панели

## 🚀 Установка
> Для работы парсера необходимо установить браузер [Google Chrome](https://google.com/chrome).

### Установка этого форка из исходников
Дистрибутив форка называется **`parser-2gis-new`** (import-пакет остался `parser_2gis`).
  ```bash
  git clone <этот-репозиторий>
  cd parser-2gis-new
  python -m venv .venv
  pip install -e .
  ```
  Запуск (доступны обе команды — `parser-2gis-new` и `parser-2gis`):
  - `parser-2gis-new` — **веб-интерфейс** в браузере (по умолчанию);
  - `parser-2gis-new -i <URL> -o out.csv -f csv` — CLI без браузера.

  > Десктоп-GUI (tkinter/PySimpleGUI) в этом форке удалён — весь интерфейс перенесён в браузер.

### Оригинальный проект (PyPI)
  ```bash
  pip install parser-2gis        # CLI оригинального parser-2gis
  pip install parser-2gis[gui]   # с десктоп-GUI
  ```

## 📖 Документация
Описание работы доступно на [вики](https://github.com/interlark/parser-2gis/wiki).

## 🔧 Изменения форка

Форк сохраняет всю функциональность оригинала и добавляет:

- **Модернизация:** переход на `pydantic` v2, поддержка Python 3.12/3.13, обновлённые сборочные зависимости.
- **Фикс парсинга:** в headless-режиме карта 2GIS (WebGL) не инициализировалась, из-за чего страница отправляла вырождённый viewport и API отвечал `400 «Bound is incorrect»`. Исправлено через новый headless-режим Chrome и принудительный размер вьюпорта.
- **Веб-интерфейс — единственный UI.** Десктоп-GUI (tkinter/PySimpleGUI) удалён, все его функции перенесены в браузер. Запуск без аргументов открывает дашборд. Flask стал основной зависимостью.
- **Генератор ссылок в вебе:** выбор страны, города (мультивыбор) и рубрики (поиск по 1785 рубрикам) → готовые URL 2GIS добавляются в список направлений.
- **Расширенные настройки в вебе:** лимит RAM браузера, задержка кликов, «точные совпадения», кодировка, CSV-опции (рубрики, комментарии, пустые колонки, дубликаты, колонок на поле).
- **Фильтры результатов:** дедуп франшиз (1 филиал на организацию), только с телефоном/WhatsApp/соцсетями/e-mail/сайтом, по рейтингу и количеству отзывов. Работают для всех форматов; доступны в CLI (`--filters.*`) и в вебе.
- **Чистый вид CSV/XLSX** (`--writer.csv.clean`) — только основные читаемые колонки.
- **Новый формат HTML** (`-f html`) — самодостаточная страница с карточками и кнопками WhatsApp / звонок / 2GIS / соцсети и поиском.
- **Улучшенный XLSX** — кликабельные ссылки, авто-ширина колонок, заморозка шапки, автофильтр.

Полный список — в [CHANGELOG.md](CHANGELOG.md).

## 📜 Лицензия и авторство

- Оригинальный проект: **parser-2gis** — © **Andy Trofimov** (interlark@gmail.com),
  https://github.com/interlark/parser-2gis
- Лицензия: **GNU LGPLv3** (см. [LICENSE](LICENSE)) — сохранена без изменений.
- Модификации в этом форке распространяются на тех же условиях LGPLv3.
