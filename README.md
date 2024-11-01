# Weather Prediction Teleagram Bot
Это TG бот + Flask-приложение для прогноза погоды, на основе AccuWeather API.
## Описание
Приложение позволяет пользователю вводить начальную и конечную точки маршрута, а также промежуточные точки, чтобы получить данные о погоде для каждого из них. Приложение использует API от AccuWeather для получения информации о температуре, влажности и других погодных данных.
## Начало работы
### 1. Клонирование репозитория
Клонируйте репозиторий и перейдите в его директорию:
```
git clone https://github.com/VaVaRenik/Weather_Predictions.git
cd Weather_Prediction
```
### 2. Создание и активация виртуального окружения
```python -m venv venv```
На Windows:
```venv\Scripts\activate```
На На macOS/Linux:
```source venv/bin/activate```
### 3. Установка зависимостей
```pip install -r requirements.txt```
### 4. Пробросьте ваш ключ от AccuWeatherAPI и токен телеграм бота
Создайте файл ```.env```, и вставьте в него ```API_KEY=your_accuweather_api_key```, ```BOT_TOKEN=your_tg_bot_token```
### 5. Запуск программ
Если нужно запустить только web сервис, то запускайте ```App.app```, если tg bot, то ```Bot.bot```
