from datetime import datetime
import plotly.graph_objects as go


class Weather:
    def __init__(self, city_name, weather_data):
        self.city_name = city_name
        self.local_observation_time = datetime.fromisoformat(weather_data.get('LocalObservationDateTime')) # datetime
        self.temperature_celsius = weather_data['Temperature']['Metric']['Value']  # Градусы в цельсиях
        self.humidity = weather_data['RelativeHumidity']  # Влажность
        self.wind_speed = weather_data['Wind']['Speed']['Metric']['Value']  # Скорость ветра
        self.has_precipitation = weather_data['HasPrecipitation']  # Есть осадки
        self.precipitation_probability = (
                weather_data['PrecipitationSummary']['Precipitation'][
                    'Metric']['Value'] * 100)  # Вероятность осадков
        self.visibility = weather_data['Visibility']['Metric']['Value']  # Видимость
        self.pressure = weather_data['Pressure']['Metric']['Value']  # Давление
        self.apparent_temperature = weather_data['ApparentTemperature']['Metric']['Value']  # Ощущаемая температура

    def display_weather_info(self) -> str:
        """
        Возвращает информацию о погоде
        """
        weather_info = (
            f"Время наблюдения: {self.local_observation_time.strftime("%d.%m.%Y, %H:%M")}<br>"
            f"Температура (°C): {self.temperature_celsius}<br>"
            f"Ощущаемая температура (°C): {self.apparent_temperature}<br>"
            f"Влажность (%): {self.humidity}<br>"
            f"Скорость ветра (км/ч): {self.wind_speed}<br>"
            f"Осадки: {'Да' if self.has_precipitation else 'Нет'}<br>"
            f"Вероятность осадков (%): {self.precipitation_probability}<br>"
            f"Видимость (км): {self.visibility}<br>"
            f"Давление (гПа): {self.pressure}<br>"
        )
        return weather_info


    def display_weather_info_html(self):
        return f"""
            <tr><th>Время наблюдения</th><td>{self.local_observation_time.strftime("%d.%m.%Y, %H:%M")}</td></tr>
            <tr><th>Температура (°C)</th><td>{self.temperature_celsius}</td></tr>
            <tr><th>Ощущаемая температура (°C)</th><td>{self.apparent_temperature}</td></tr>
            <tr><th>Влажность (%)</th><td>{self.humidity}</td></tr>
            <tr><th>Скорость ветра (км/ч)</th><td>{self.wind_speed}</td></tr>
            <tr><th>Осадки</th><td>{'Есть' if self.has_precipitation else 'Нет'}</td></tr>
            <tr><th>Вероятность осадков (%)</th><td>{self.precipitation_probability}</td></tr>
            <tr><th>Видимость (км)</th><td>{self.visibility}</td></tr>
            <tr><th>Давление (гПа)</th><td>{self.pressure}</td></tr>
            """

    def display_weather_for_tg(self):
        return (
            f"*Место:* {self.city_name}\n"
            f"*Время наблюдения:* {self.local_observation_time.strftime('%d.%m.%Y, %H:%M')}\n"
            f"*Температура (°C):* {self.temperature_celsius}\n"
            f"*Ощущаемая температура (°C):* {self.apparent_temperature}\n"
            f"*Влажность (%):* {self.humidity}\n"
            f"*Скорость ветра (км/ч):* {self.wind_speed}\n"
            f"*Осадки:* {'Есть' if self.has_precipitation else 'Нет'}\n"
            f"*Вероятность осадков (%):* {self.precipitation_probability}\n"
            f"*Видимость (км):* {self.visibility}\n"
            f"*Давление (гПа):* {self.pressure}"
        )

    def is_weather_bad(self):
        """
        Определяет плохие погодные условия на основе различных критериев.
        Возвращает True, если погода считается плохой, иначе False.
        """
        if any([
            self.temperature_celsius > 35,  # Слишком жарко
            self.temperature_celsius < -5,  # Слишком холодно
            self.apparent_temperature < -10,  # Очень холодно по ощущениям
            self.wind_speed > 50,  # Сильный ветер
            self.visibility < 2,  # Плохая видимость
            self.humidity > 90,  # Очень высокая влажность
            self.has_precipitation or self.precipitation_probability >= 70,  # Высокая вероятность осадков
            self.pressure < 980,  # Низкое давление (может означать шторм)
        ]):
            return True
        return False

    def create_temperature_fig(self):
        if self.temperature_celsius > 30 or self.temperature_celsius < -30:
            return None

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=self.temperature_celsius,  # Используем среднюю температуру
            title={'text': 'Temperature (°C)'},
            gauge={
                'axis': {'range': [-30, 30]},  # Диапазон от -30 до +30
                'steps': [
                    {'range': [-30, -10], 'color': "lightblue"},
                    # Холодные температуры
                    {'range': [-10, 10], 'color': "palegreen"},
                    # Умеренные температуры
                    {'range': [10, 20], 'color': "khaki"},  # Тепло
                    {'range': [20, 30], 'color': "tomato"}
                    # Жаркие температуры
                ],
                'threshold': {
                    'line': {'color': 'darkred', 'width': 4},
                    # Настройка пороговой линии
                    'thickness': 0.75,
                    'value': self.temperature_celsius  # Значение средней температуры
                }
            }
        ))

        fig.update_layout(
            title="Temperature Status",
            height=400
        )

        return fig
