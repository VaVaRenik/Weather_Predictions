from flask import Flask, render_template, request
import requests
from Class_Weather.weather import Weather
import plotly.express as px
import pandas as pd
import os
from dotenv import load_dotenv


app = Flask(__name__)

load_dotenv()

api_key = os.getenv("API_KEY")


def get_location_key(city_name: str) -> str or None:
    """"
    Принимает название города, возвращает Location Key для него
    """
    base_url = "http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {
        'apikey': api_key,
        'q': city_name
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()

        data = response.json()

        if data:
            location_key = data[0]["Key"]
            return location_key
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None


def get_weather_from_loc_key(location_key: str) -> dict or None:
    """
    Принимает Location Key и возвращает погодные условия
    """
    weather_url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}'
    params = {
        'apikey': api_key,
        'details': 'true'
    }

    try:
        response = requests.get(weather_url, params=params)
        response.raise_for_status()
        weather_data = response.json()

        if weather_data:
            return weather_data[0]
        else:
            return None
    except requests.exceptions.RequestException as e:
        return None


def get_5_daily_forecast_from_local_key(location_key: str) -> dict or None:
    base_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/5day/{location_key}"
    params = {
        "apikey": api_key
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        forecast = response.json()

        if forecast:
            return forecast
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def create_temperature_trends(df) -> px.line:
    df_melted = df.melt(id_vars="City", var_name="Date", value_name="Average Temperature (°C)")

    fig = px.line(df_melted, x="Date", y="Average Temperature (°C)", color="City", title="Temperature Trends",
                  markers=True)

    # Customize the axes titles
    fig.update_xaxes(title="Date")
    fig.update_yaxes(title="Temperature (°C)")

    # Customize the line and marker styles
    fig.update_traces(
        line=dict(width=3),  # Adjust line width
        marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey'))  # Adjust marker size and outline
    )

    # Customize the legend
    fig.update_layout(
        legend_title_text='City',
        height=600,
        width=1000
    )

    return fig


def get_location_key_and_weather(city) -> (str, Weather):
    """
    Принимает название города и возвращает его location key и этот город в виде Weather
    """

    try:
        location_key = get_location_key(city)

        if not location_key:
            return None

        weather_data = get_weather_from_loc_key(location_key)

        if not weather_data:
            return None

        weather = Weather(city_name=city, weather_data=weather_data)

    except Exception:
        return None

    return location_key, weather


def create_weather_df_from_forecast(weather_data: dict, city_name: str) -> pd.DataFrame:
    daily_forecasts = weather_data['DailyForecasts']

    weather_info = {"City": city_name}
    for forecast in daily_forecasts[:5]:  # ограничиваем до первых 5 дней
        date = forecast['Date'][:10]  # получаем дату в формате YYYY-MM-DD
        temp_min = forecast['Temperature']['Minimum']['Value']
        temp_max = forecast['Temperature']['Maximum']['Value']
        avg_temp = (temp_min + temp_max) / 2  # средняя температура
        weather_info[date] = avg_temp  # добавляем в словарь

    df = pd.DataFrame([weather_info])

    return df


def create_forecasts_df(cities: list, location_keys: list) -> pd.DataFrame:
    answer = pd.DataFrame()

    for city, location_key in zip(cities, location_keys):
        forecast = get_5_daily_forecast_from_local_key(location_key)
        df = create_weather_df_from_forecast(forecast, city)
        answer = pd.concat([answer, df], ignore_index=True)

    return answer


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/check-weather", methods=["GET", "POST"])
def check_weather():
    html_form = "index.html"
    if request.method == "POST":
        # Получаем данные из формы
        start_city = request.form.get("start_city")
        end_city = request.form.get("end_city")
        stop_cities = request.form.getlist("stop_city")
    else:
        # Получаем данные из параметров URL
        start_city = request.args.get("start_city")
        end_city = request.args.get("end_city")
        stop_cities = request.args.get("stop_cities", "").split(",")
        html_form = "graphics.html"

    result, data = process_weather_check(start_city, end_city, stop_cities)
    if data:
        return render_template(
            html_form,
            result=result.strip,
            start_weather_info=data["start_weather_info"],
            end_weather_info=data["end_weather_info"],
            stop_weather_infos=data["stop_weather_infos"],
            temperature_trends_json=data["temperature_trends_json"],
            start_gauge_json=data["start_gauge_json"],
            end_gauge_json=data["end_gauge_json"],
        )
    else:
        return render_template("index.html", result=result)


def process_weather_check(start_city, end_city, stop_cities):
    try:
        # Получаем информацию для начальной точки
        start_location_key, start_weather = get_location_key_and_weather(start_city)
        if start_location_key is None or start_weather is None:
            return f"Не удалось найти город {start_city}", None

        # Получаем информацию для конечной точки
        end_location_key, end_weather = get_location_key_and_weather(end_city)
        if end_location_key is None or end_weather is None:
            return f"Не удалось найти город {end_city}", None

        # Получаем информацию о промежуточных точках
        stop_location_keys = []
        stop_weathers = []
        stop_weather_infos = []
        for stop_city in stop_cities:
            loc_key, weather = get_location_key_and_weather(stop_city)
            if loc_key is None or weather is None:
                return f"Не удалось найти город {stop_city}", None
            stop_location_keys.append(loc_key)
            stop_weathers.append(weather)
            stop_weather_infos.append(weather.display_weather_info_html())

        # Создаем список городов и их location_keys
        all_cities = [start_city] + stop_cities + [end_city]
        all_keys = [start_location_key] + stop_location_keys + [end_location_key]

        # Создаем df для основного графика
        forecast_df = create_forecasts_df(all_cities, all_keys)
        temperature_trends_fig = create_temperature_trends(forecast_df)
        temperature_trends_json = temperature_trends_fig.to_json()

        # Генерируем списки JSON для побочных графиков
        start_gauge_fig_json = start_weather.create_temperature_fig().to_json()
        end_gauge_fig_json = end_weather.create_temperature_fig().to_json()
        stop_gauges = [weather.create_temperature_fig().to_json() for weather in stop_weathers]

        # Проверяем плохие погодные условия
        start_weather_bad = start_weather.is_weather_bad()
        end_weather_bad = end_weather.is_weather_bad()
        stop_weather_bad = any(weather.is_weather_bad() for weather in stop_weathers)

        if start_weather_bad or end_weather_bad or stop_weather_bad:
            result = "Есть плохие погодные условия на маршруте, рекомендуем выбрать другой день"
        else:
            result = "Погода благоприятная на всем маршруте!"

        stop_data = [{"city": city, "weather": weather_html, "gauge_json": fig}
                     for city, weather_html, fig in zip(stop_cities, stop_weather_infos, stop_gauges)]

        # Если запрос пришел от Telegram-бота, возвращаем данные в JSON
        weather_data = {
            "start_weather_info": start_weather.display_weather_info_html(),
            "end_weather_info": end_weather.display_weather_info_html(),
            "stop_weather_infos": stop_data,
            "temperature_trends_json": temperature_trends_json,
            "start_gauge_json": start_gauge_fig_json,
            "end_gauge_json": end_gauge_fig_json,
        }

        return result, weather_data

    except Exception as e:
        return f"Произошла ошибка: {e}, попробуйте снова.", None


if __name__ == "__main__":
    app.run()