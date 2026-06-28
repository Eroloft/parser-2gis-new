<p align="center">
  <a href="#%E2%84%B9%EF%B8%8F-%D0%BE%D0%BF%D0%B8%D1%81%D0%B0%D0%BD%D0%B8%D0%B5">
    <img alt="Logo" width="128" src="https://user-images.githubusercontent.com/20641837/174094285-6e32eb04-7feb-4a60-bddf-5a0fde5dba4d.png"/>
  </a>
</p>
<h1 align="center">Parser2GIS</h1>

<p align="center">
  <a href="https://github.com/interlark/parser-2gis/actions/workflows/tests.yml"><img src="https://github.com/interlark/parser-2gis/actions/workflows/tests.yml/badge.svg" alt="Tests"/></a>
  <a href="https://pypi.org/project/parser-2gis"><img src="https://badgen.net/pypi/v/parser-2gis" alt="PyPi version"/></a>
  <a href="https://pypi.org/project/parser-2gis"><img src="https://badgen.net/pypi/python/parser-2gis" alt="Supported Python versions"/></a>
  <a href="https://github.com/interlark/parser-2gis/releases"><img src="https://img.shields.io/github/downloads/interlark/parser-2gis/total.svg" alt="Downloads"/></a>
</p>

> ### 🍴 Это форк
> Проект является форком [**parser-2gis**](https://github.com/interlark/parser-2gis)
> (© Andy Trofimov, лицензия LGPLv3). Оригинальная разработка принадлежит автору;
> здесь добавлены модификации — см. раздел [«Изменения форка»](#-изменения-форка)
> и [CHANGELOG](CHANGELOG.md). Это независимый форк, не одобрен и не поддерживается
> оригинальным автором.

**Parser2GIS** - парсер сайта [2GIS](https://2gis.ru/) с помощью браузера [Google Chrome](https://google.com/chrome).

<img alt="Screenshot" src="https://user-images.githubusercontent.com/20641837/174098241-7c0874aa-e70d-4978-86dc-7fd90af44603.png"/>

## ℹ️ Описание

Парсер для автоматического сбора базы адресов и контактов предприятий, которые работают на территории
России <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511175-3d47f0f0-4e3f-45d2-8495-95d0612a8a8c.svg"/>, Казахстана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511625-20420aef-59c3-426d-a112-654d2caf0dda.svg"/>, Беларуси <img width="18px" src="https://user-images.githubusercontent.com/20641837/183511940-ce088ad1-d97f-4fa1-849a-9b887ad481c5.svg"/>,
Азербайджана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512176-1f6795a1-ceac-4865-a29f-b5720ce5115e.svg"/>, Киргизии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512234-286ca403-5194-4a6d-a59e-59201140078a.svg"/>, Узбекистана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512333-7ec1f36d-07fe-450d-b6f1-eed59a3b69c8.svg"/>, Чехии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512458-5a5d9531-a8f0-4624-99da-7069cde84926.svg"/>, Египта <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512581-71fa2106-8cc1-43cc-a680-b3ff420acb8a.svg"/>, Италии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512763-0b438e5b-3ff0-4717-a826-0baac9207167.svg"/>, Саудовской Аравии <img width="18px" src="https://user-images.githubusercontent.com/20641837/183512980-427a985a-df1b-42c8-90bb-2c61692b6654.svg"/>, Кипра <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513128-4367d2b1-feb9-4efe-bc57-73a15d178ef2.svg"/>, Объединенных Арабских Эмиратов <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513374-9afef8c7-923e-4a18-9cd8-c69645b99377.svg"/>, Чили <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513576-7209ce90-a04a-4258-9832-ef210198c3c4.svg"/>, Катара <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513757-143ee2bf-b66c-4766-bbe1-db896a33eac1.svg"/>, Омана <img width="18px" src="https://user-images.githubusercontent.com/20641837/183513865-27509b74-b08f-4d92-b83b-a0d3aaabe155.svg"/>, Бахрейна <img width="18px" src="https://user-images.githubusercontent.com/20641837/183514076-3b6c9496-7c95-4452-8ee1-8723d98f876d.svg"/>, Кувейта <img width="18px" src="https://user-images.githubusercontent.com/20641837/183514240-7eff8632-5cd2-46ac-bed4-e483bb2df5f0.svg"/>.

## ✨ Особенности
- 💰 Абсолютно бесплатный
- 🤖 Успешно обходит анти-бот блокировки на территории РФ
- 🖥️ Работает под Windows, Linux и MacOS
- 📄 Четыре выходных формата: CSV таблица, XLSX таблица, JSON список и **HTML-страница**
- 🔗 Наличие генератора ссылок по городам и рубрикам
- 🌐 **Современный веб-интерфейс** в браузере (`parser-2gis --web`)
- 🧹 **Фильтры результатов:** без франшиз (1 филиал на организацию), только с телефоном / WhatsApp / соцсетями / e-mail / сайтом, по рейтингу и отзывам
- 💬 **HTML-страница с кнопками WhatsApp и 2GIS** — открыл и сразу пишешь клиентам
- ✨ **Чистый вид** вывода — только нужные колонки, без мусора

## 🚀 Установка
> Для работы парсера необходимо установить браузер [Google Chrome](https://google.com/chrome).

### Установка этого форка из исходников
Дистрибутив форка называется **`parser-2gis-new`** (import-пакет остался `parser_2gis`).
  ```bash
  git clone <этот-репозиторий>
  cd parser-2gis-new
  python -m venv .venv
  # CLI + GUI + веб-интерфейс
  pip install -e ".[gui,web]"
  ```
  Запуск (доступны обе команды — `parser-2gis` и `parser-2gis-new`):
  `parser-2gis-new` (GUI), `parser-2gis-new --web` (браузер) или
  `parser-2gis-new -i <URL> -o out.csv -f csv` (CLI).

  > GUI использует [FreeSimpleGUI](https://pypi.org/project/FreeSimpleGUI/) — поддерживаемый
  > open-source форк PySimpleGUI (оригинальный пин `PySimpleGUI==4.59.0` был удалён из PyPI).

### Оригинальный проект (PyPI)
  ```bash
  # CLI / CLI + GUI оригинального parser-2gis
  pip install parser-2gis
  pip install parser-2gis[gui]
  ```

## 📖 Документация
Описание работы доступно на [вики](https://github.com/interlark/parser-2gis/wiki).

## 🔧 Изменения форка

Форк сохраняет всю функциональность оригинала и добавляет:

- **Модернизация:** переход на `pydantic` v2, GUI на `FreeSimpleGUI` вместо снятого с PyPI `PySimpleGUI`, поддержка Python 3.12/3.13, обновлённые сборочные зависимости.
- **Фикс парсинга:** в headless-режиме карта 2GIS (WebGL) не инициализировалась, из-за чего страница отправляла вырождённый viewport и API отвечал `400 «Bound is incorrect»`. Исправлено через новый headless-режим Chrome и принудительный размер вьюпорта.
- **Фильтры результатов:** дедуп франшиз (1 филиал на организацию), только с телефоном/WhatsApp/соцсетями/e-mail/сайтом, по рейтингу и количеству отзывов. Работают для всех форматов; доступны в CLI (`--filters.*`), десктоп-GUI и веб-интерфейсе.
- **Чистый вид CSV/XLSX** (`--writer.csv.clean`) — только основные читаемые колонки.
- **Новый формат HTML** (`-f html`) — самодостаточная страница с карточками и кнопками WhatsApp / звонок / 2GIS / соцсети и поиском.
- **Улучшенный XLSX** — кликабельные ссылки, авто-ширина колонок, заморозка шапки, автофильтр.
- **Веб-интерфейс** (`parser-2gis --web`) — современный локальный дашборд: список направлений, фильтры, запуск/стоп, живой прогресс, карточки результатов и экспорт.

Полный список — в [CHANGELOG.md](CHANGELOG.md).

## 📜 Лицензия и авторство

- Оригинальный проект: **parser-2gis** — © **Andy Trofimov** (interlark@gmail.com),
  https://github.com/interlark/parser-2gis
- Лицензия: **GNU LGPLv3** (см. [LICENSE](LICENSE)) — сохранена без изменений.
- Модификации в этом форке распространяются на тех же условиях LGPLv3.

## 👍 Поддержать проект
<a href="https://yoomoney.ru/to/4100118362270186" target="_blank">
  <img alt="Yoomoney Donate" src="https://github.com/interlark/parser-2gis/assets/20641837/e875e948-0d69-4ed5-804c-8a1736ab0c9d" width="150">
</a>
