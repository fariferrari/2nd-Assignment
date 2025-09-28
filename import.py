import psycopg2 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from datetime import datetime

# Удаляем старую папку и создаем новую
if os.path.exists('charts'):
    import shutil
    shutil.rmtree('charts')
os.makedirs('charts')

# Настройка стиля графиков
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def execute_query_to_df(query, description):
    """Выполняет SQL-запрос и возвращает DataFrame"""
    try:
        with psycopg2.connect( 
            host="localhost",
            database="airport_db",
            user="postgres",
            password="farida",  
            port="5432"
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                df = pd.DataFrame(results, columns=columns)
                print(f"✓ {description}: получено {len(df)} строк")
                return df
    except Exception as e:
        print(f"✗ Ошибка в запросе '{description}': {e}")
        return None

def create_visualizations():
    """Создает 6 различных визуализаций"""
    
    # 1. КРУГОВАЯ ДИАГРАММА - Распределение статусов рейсов
    print("\n" + "="*80)
    print("1. КРУГОВАЯ ДИАГРАММА: Распределение статусов рейсов")
    
    query_pie = """
    SELECT 
        status,
        COUNT(*) as count_flights,
        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM flights), 1) as percentage
    FROM flights 
    WHERE status IS NOT NULL
    GROUP BY status
    ORDER BY count_flights DESC;
    """
    
    df_pie = execute_query_to_df(query_pie, "Статусы рейсов")
    if df_pie is not None and len(df_pie) > 0:
        plt.figure(figsize=(12, 8))
        
        # Создаем круговую диаграмму
        colors = ['#4CAF50', '#FF9800', '#F44336', '#2196F3']  # Зеленый, оранжевый, красный, синий
        wedges, texts, autotexts = plt.pie(df_pie['count_flights'], 
                                          labels=df_pie['status'],
                                          autopct='%1.1f%%',
                                          startangle=90,
                                          colors=colors[:len(df_pie)],
                                          explode=[0.05] * len(df_pie))
        
        # Улучшаем подписи
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(10)
        
        plt.title('РАСПРЕДЕЛЕНИЕ СТАТУСОВ РЕЙСОВ\n(все авиакомпании)', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.savefig('charts/pie_chart_status_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: pie_chart_status_distribution.png")

    # 2. СТОЛБЧАТАЯ ДИАГРАММА - Топ авиакомпаний по количеству рейсов
    print("\n" + "="*80)
    print("2. СТОЛБЧАТАЯ ДИАГРАММА: Топ авиакомпаний по рейсам")
    
    query_bar = """
    SELECT 
        a.airline_name,
        a.airline_country,
        COUNT(f.flight_id) as total_flights,
        ROUND(COUNT(CASE WHEN f.status = 'On Time' THEN 1 END) * 100.0 / COUNT(f.flight_id), 1) as on_time_percent
    FROM flights f
    JOIN airline a ON f.airline_id = a.airline_id
    GROUP BY a.airline_id, a.airline_name, a.airline_country
    HAVING COUNT(f.flight_id) >= 5
    ORDER BY total_flights DESC
    LIMIT 10;
    """
    
    df_bar = execute_query_to_df(query_bar, "Топ авиакомпаний")
    if df_bar is not None and len(df_bar) > 0:
        plt.figure(figsize=(14, 8))
        
        # Создаем столбчатую диаграмму
        bars = plt.bar(range(len(df_bar)), df_bar['total_flights'], 
                      color=plt.cm.viridis(np.linspace(0, 1, len(df_bar))),
                      alpha=0.8, edgecolor='black', linewidth=0.5)
        
        # Настраиваем оси и подписи
        plt.xticks(range(len(df_bar)), [name[:20] + '...' if len(name) > 20 else name 
                                      for name in df_bar['airline_name']], rotation=45, ha='right')
        plt.ylabel('Количество рейсов', fontsize=12, fontweight='bold')
        plt.xlabel('Авиакомпании', fontsize=12, fontweight='bold')
        plt.title('ТОП-10 АВИАКОМПАНИЙ ПО КОЛИЧЕСТВУ РЕЙСОВ', fontsize=16, fontweight='bold')
        
        # Добавляем значения на столбцы
        for i, (bar, count, percent) in enumerate(zip(bars, df_bar['total_flights'], df_bar['on_time_percent'])):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(df_bar['total_flights'])*0.01,
                    f'{int(count)}\n({percent}%)', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        plt.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig('charts/bar_chart_top_airlines.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: bar_chart_top_airlines.png")

    # 3. ГОРИЗОНТАЛЬНАЯ СТОЛБЧАТАЯ ДИАГРАММА - Загруженность аэропортов
    print("\n" + "="*80)
    print("3. ГОРИЗОНТАЛЬНАЯ СТОЛБЧАТАЯ: Загруженность аэропортов")
    
    query_hbar = """
    SELECT 
        ap.airport_name,
        ap.city,
        ap.country,
        COUNT(DISTINCT f.flight_id) as total_flights,
        COUNT(DISTINCT CASE WHEN f.departure_airport_id = ap.airport_id THEN f.flight_id END) as departures,
        COUNT(DISTINCT CASE WHEN f.arrival_airport_id = ap.airport_id THEN f.flight_id END) as arrivals
    FROM airport ap
    LEFT JOIN flights f ON ap.airport_id = f.departure_airport_id OR ap.airport_id = f.arrival_airport_id
    GROUP BY ap.airport_id, ap.airport_name, ap.city, ap.country
    HAVING COUNT(DISTINCT f.flight_id) > 0
    ORDER BY total_flights DESC
    LIMIT 15;
    """
    
    df_hbar = execute_query_to_df(query_hbar, "Загруженность аэропортов")
    if df_hbar is not None and len(df_hbar) > 0:
        plt.figure(figsize=(14, 10))
        
        y_pos = np.arange(len(df_hbar))
        
        # Создаем групповую горизонтальную диаграмму
        plt.barh(y_pos - 0.2, df_hbar['departures'], height=0.4, label='Вылеты', alpha=0.8, color='#FF6B6B')
        plt.barh(y_pos + 0.2, df_hbar['arrivals'], height=0.4, label='Прилеты', alpha=0.8, color='#4ECDC4')
        
        # Настраиваем ось Y
        plt.yticks(y_pos, [f"{row['airport_name']}\n({row['city']})" 
                          for _, row in df_hbar.iterrows()])
        plt.xlabel('Количество рейсов', fontsize=12, fontweight='bold')
        plt.title('ТОП-15 САМЫХ ЗАГРУЖЕННЫХ АЭРОПОРТОВ\n(разделение по вылетам и прилетам)', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.legend()
        plt.gca().invert_yaxis()
        plt.grid(axis='x', alpha=0.3)
        plt.tight_layout()
        plt.savefig('charts/hbar_chart_busiest_airports.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: hbar_chart_busiest_airports.png")

    # 4. ЛИНЕЙНЫЙ ГРАФИК - Сезонность перевозок (исправленный)
    print("\n" + "="*80)
    print("4. ЛИНЕЙНЫЙ ГРАФИК: Сезонность перевозок")
    
    query_line = """
    WITH month_flights AS (
        SELECT 
            EXTRACT(MONTH FROM b.created_at) as month_num,
            TO_CHAR(b.created_at, 'Month') as month_name,
            COUNT(DISTINCT b.booking_id) as bookings_count
        FROM booking b
        JOIN booking_flight bf ON b.booking_id = bf.booking_id
        JOIN flights f ON bf.flight_id = f.flight_id
        WHERE b.created_at IS NOT NULL
        GROUP BY EXTRACT(MONTH FROM b.created_at), TO_CHAR(b.created_at, 'Month')
    )
    SELECT month_num, month_name, bookings_count
    FROM month_flights
    ORDER BY month_num;
    """
    
    df_line = execute_query_to_df(query_line, "Бронирования по месяцам")
    if df_line is not None and len(df_line) > 0:
        plt.figure(figsize=(14, 8))
        
        # Создаем линейный график
        plt.plot(df_line['month_num'], df_line['bookings_count'], 
                marker='o', linewidth=3, markersize=8, markerfacecolor='red', 
                markeredgecolor='black', markeredgewidth=1)
        
        # Настраиваем график
        plt.xticks(df_line['month_num'], df_line['month_name'].str.strip())
        plt.ylabel('Количество бронирований', fontsize=12, fontweight='bold')
        plt.xlabel('Месяц', fontsize=12, fontweight='bold')
        plt.title('СЕЗОННОСТЬ АВИАПЕРЕВОЗОК\n(по количеству бронирований)', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3)
        
        # Добавляем значения точек
        for x, y in zip(df_line['month_num'], df_line['bookings_count']):
            plt.text(x, y + max(df_line['bookings_count']) * 0.02, f'{int(y)}', 
                    ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        plt.tight_layout()
        plt.savefig('charts/line_chart_seasonality.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: line_chart_seasonality.png")

    # 5. ГИСТОГРАММА - Распределение количества рейсов на пассажира
    print("\n" + "="*80)
    print("5. ГИСТОГРАММА: Активность пассажиров")
    
    query_hist = """
    SELECT 
        p.passenger_id,
        COUNT(DISTINCT bf.flight_id) as flights_count
    FROM passengers p
    JOIN booking b ON p.passenger_id = b.passenger_id
    JOIN booking_flight bf ON b.booking_id = bf.booking_id
    GROUP BY p.passenger_id
    HAVING COUNT(DISTINCT bf.flight_id) > 0;
    """
    
    df_hist = execute_query_to_df(query_hist, "Активность пассажиров")
    if df_hist is not None and len(df_hist) > 0:
        plt.figure(figsize=(14, 8))
        
        # Создаем гистограмму
        n, bins, patches = plt.hist(df_hist['flights_count'], bins=15, 
                                   alpha=0.7, color='#9B59B6', edgecolor='black', linewidth=0.5)
        
        plt.xlabel('Количество рейсов на пассажира', fontsize=12, fontweight='bold')
        plt.ylabel('Количество пассажиров', fontsize=12, fontweight='bold')
        plt.title('РАСПРЕДЕЛЕНИЕ АКТИВНОСТИ ПАССАЖИРОВ\n(сколько рейсов совершает один пассажир)', 
                 fontsize=16, fontweight='bold', pad=20)
        plt.grid(True, alpha=0.3)
        
        # Добавляем статистику
        mean_val = df_hist['flights_count'].mean()
        median_val = df_hist['flights_count'].median()
        plt.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Среднее: {mean_val:.1f}')
        plt.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Медиана: {median_val:.1f}')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('charts/histogram_passenger_activity.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: histogram_passenger_activity.png")

    # 6. ДИАГРАММА РАССЕЯНИЯ - Связь между рейсами и пассажирами по странам
    print("\n" + "="*80)
    print("6. ДИАГРАММА РАССЕЯНИЯ: Активность по странам")
    
    query_scatter = """
    SELECT 
        p.country_of_residence as country,
        COUNT(DISTINCT p.passenger_id) as passengers_count,
        COUNT(DISTINCT bf.flight_id) as unique_flights,
        COUNT(b.booking_id) as total_bookings
    FROM passengers p
    JOIN booking b ON p.passenger_id = b.passenger_id
    JOIN booking_flight bf ON b.booking_id = bf.booking_id
    GROUP BY p.country_of_residence
    HAVING COUNT(DISTINCT p.passenger_id) >= 3
    ORDER BY passengers_count DESC;
    """
    
    df_scatter = execute_query_to_df(query_scatter, "Активность по странам")
    if df_scatter is not None and len(df_scatter) > 0:
        plt.figure(figsize=(14, 10))
        
        # Создаем диаграмму рассеяния
        scatter = plt.scatter(df_scatter['passengers_count'], 
                             df_scatter['unique_flights'],
                             s=df_scatter['total_bookings']*2,  # Размер точек по бронированиям
                             c=df_scatter['total_bookings'],    # Цвет по бронированиям
                             alpha=0.6, cmap='viridis', edgecolors='black', linewidth=0.5)
        
        plt.xlabel('Количество пассажиров из страны', fontsize=12, fontweight='bold')
        plt.ylabel('Количество уникальных рейсов', fontsize=12, fontweight='bold')
        plt.title('АКТИВНОСТЬ ПАССАЖИРОВ ПО СТРАНАМ\n(размер точки = количество бронирований)', 
                 fontsize=16, fontweight='bold', pad=20)
        
        # Добавляем цветовую шкалу
        cbar = plt.colorbar(scatter)
        cbar.set_label('Количество бронирований', fontweight='bold')
        
        # Добавляем подписи для крупных стран
        for i, row in df_scatter.iterrows():
            if row['passengers_count'] > df_scatter['passengers_count'].median():
                plt.annotate(row['country'], 
                            (row['passengers_count'], row['unique_flights']),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, fontweight='bold', alpha=0.8)
        
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig('charts/scatter_country_activity.png', dpi=300, bbox_inches='tight')
        plt.close()
        print("✓ Создан график: scatter_country_activity.png")

def main():
    print("🚀 НАЧИНАЕМ СОЗДАНИЕ ГРАФИКОВ...")
    print("="*80)
    
    try:
        create_visualizations()
        
        print("\n" + "="*80)
        print("✅ ВСЕ ГРАФИКИ УСПЕШНО СОЗДАНЫ!")
        print("📁 Папка 'charts' содержит:")
        
        if os.path.exists('charts'):
            files = os.listdir('charts')
            for i, file in enumerate(files, 1):
                print(f"   {i}. {file}")
        else:
            print("   Папка charts не найдена")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main() 