import pandas as pd
import matplotlib.pyplot as plt
import joblib

# Load the Prophet model
import os


# Get the absolute path
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "models", "line4", "prophet_r04.pkl")

print("Full path to model:", model_path)
print("Does file exist?:", os.path.exists(model_path))

# Use the absolute path for loading
model = joblib.load(model_path)


# Generate future dates
future_dates = pd.date_range(start="2025-02-06 13:00", end="2025-02-06 14:00", periods=30)
future_df = pd.DataFrame({"ds": future_dates})
future_df["ds"] = future_df["ds"].dt.tz_localize(None)

# Make forecast
forecast = model.predict(future_df)

# Method 1: Print key statistics
print("=== Forecast Bounds Summary ===")
print(f"Average Lower Bound: {forecast['yhat_lower'].mean():.2f}°C")
print(f"Average Prediction: {forecast['yhat'].mean():.2f}°C")
print(f"Average Upper Bound: {forecast['yhat_upper'].mean():.2f}°C")
print("\n=== Range of Bounds ===")
print(f"Lower Bound Range: {forecast['yhat_lower'].min():.2f}°C to {forecast['yhat_lower'].max():.2f}°C")
print(f"Upper Bound Range: {forecast['yhat_upper'].min():.2f}°C to {forecast['yhat_upper'].max():.2f}°C")

# Method 2: Create a clean DataFrame with just the relevant columns
bounds_df = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].copy()
bounds_df.columns = ['Timestamp', 'Prediction', 'Lower_Bound', 'Upper_Bound']
bounds_df['Prediction_Range'] = bounds_df['Upper_Bound'] - bounds_df['Lower_Bound']

print("\n=== Detailed Forecast Bounds ===")
print(bounds_df.to_string(index=False))

# Method 3: Export to CSV
bounds_df.to_csv('forecast_bounds.csv', index=False)
print("\nForecast bounds exported to 'forecast_bounds.csv'")

# Method 4: Calculate confidence interval width over time
print("\n=== Confidence Interval Analysis ===")
print(f"Average interval width: {bounds_df['Prediction_Range'].mean():.2f}°C")
print(f"Maximum interval width: {bounds_df['Prediction_Range'].max():.2f}°C")
print(f"Minimum interval width: {bounds_df['Prediction_Range'].min():.2f}°C")

# Optional: Plot the bounds
plt.figure(figsize=(12, 6))
plt.plot(bounds_df['Timestamp'], bounds_df['Prediction'], 'b-', label='Forecast')
plt.plot(bounds_df['Timestamp'], bounds_df['Lower_Bound'], 'r--', label='Lower Bound')
plt.plot(bounds_df['Timestamp'], bounds_df['Upper_Bound'], 'g--', label='Upper Bound')
plt.fill_between(bounds_df['Timestamp'], 
                bounds_df['Lower_Bound'], 
                bounds_df['Upper_Bound'], 
                color='gray', 
                alpha=0.2)
plt.title('Forecast with Confidence Intervals')
plt.xlabel('Time')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()