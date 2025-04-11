import unittest
from unittest.mock import MagicMock, patch
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import joblib
from machine_learning_aadam import DatabaseManager, ForecastModel, ForecastGenerator

class EmojiTestResult(unittest.TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:
            self.stream.writeln(f"✅ {test._testMethodName}")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.showAll:
            self.stream.writeln(f"❌ {test._testMethodName}")
    
    def addError(self, test, err):
        super().addError(test, err)
        if self.showAll:
            self.stream.writeln(f"⚠️ {test._testMethodName}")

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "rakusensdatabase4"
        }
        self.db_manager = DatabaseManager(self.config)
        self.mock_conn = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

    @patch('mysql.connector.connect')
    def test_get_connection_success(self, mock_connect):
        mock_connect.return_value = "connection_obj"
        conn = self.db_manager.get_connection()
        self.assertEqual(conn, "connection_obj")

    @patch('mysql.connector.connect')
    def test_get_connection_failure(self, mock_connect):
        mock_connect.side_effect = mysql.connector.Error("DB Error")
        conn = self.db_manager.get_connection()
        self.assertIsNone(conn)

    def test_setup_forecast_table_new(self):
        self.mock_cursor.fetchone.return_value = None
        self.db_manager.setup_forecast_table(self.mock_conn, "line4")
        self.mock_cursor.execute.assert_any_call("SHOW TABLES LIKE 'forecastedline4'")
        self.mock_conn.commit.assert_called()

    def test_setup_forecast_table_existing(self):
        self.mock_cursor.fetchone.return_value = ("forecastedline5",)
        self.db_manager.setup_forecast_table(self.mock_conn, "line5")
        self.mock_cursor.execute.assert_any_call("TRUNCATE TABLE forecastedline5")
        self.mock_conn.commit.assert_called()

    def test_store_forecasts(self):
        test_forecast = {
            'yhat': 10.5,
            'yhat_lower': 9.5,
            'yhat_upper': 11.5
        }
        self.db_manager.store_forecasts(
            self.mock_conn, "line4", "r01", 
            "2025-01-01 00:00:00", test_forecast
        )
        self.mock_cursor.execute.assert_called()
        self.mock_conn.commit.assert_called()

class TestForecastModel(unittest.TestCase):
    def setUp(self):
        self.script_dir = "/test/path"
        self.forecast_model = ForecastModel(self.script_dir)
        self.mock_model = MagicMock()
        self.mock_forecast = pd.DataFrame({
            'yhat': [10.0],
            'yhat_lower': [9.0],
            'yhat_upper': [11.0]
        })
        self.mock_model.predict.return_value = self.mock_forecast

    @patch('os.path.exists', return_value=True)
    @patch('os.listdir')
    def test_detect_sensors_line4(self, mock_listdir, mock_exists):
        mock_listdir.return_value = [f"prophet_r{i:02d}.pkl" for i in range(1, 9)]
        sensors = self.forecast_model.detect_sensors("line4")
        self.assertEqual(len(sensors), 8)

    @patch('os.path.exists', return_value=True)
    @patch('os.listdir')
    def test_detect_sensors_line5(self, mock_listdir, mock_exists):
        mock_listdir.return_value = [f"prophet_r{i:02d}.pkl" for i in range(1, 18)]
        sensors = self.forecast_model.detect_sensors("line5")
        self.assertEqual(len(sensors), 17)

    @patch('os.path.exists', return_value=False)
    def test_detect_sensors_no_models(self, mock_exists):
        sensors = self.forecast_model.detect_sensors("line4")
        self.assertEqual(sensors, [])

    @patch('joblib.load')
    def test_load_model_and_forecast_success(self, mock_load):
        mock_load.return_value = self.mock_model
        forecast = self.forecast_model.load_model_and_forecast(
            "/test/path/models/line4/prophet_r01.pkl",
            datetime(2025, 1, 1, 0, 0, 0)
        )
        self.assertEqual(forecast['yhat'], 10.0)

    @patch('joblib.load')
    def test_load_model_and_forecast_failure(self, mock_load):
        mock_load.side_effect = Exception("Model error")
        forecast = self.forecast_model.load_model_and_forecast(
            "/test/path/models/line4/prophet_r01.pkl",
            datetime(2025, 1, 1, 0, 0, 0)
        )
        self.assertIsNone(forecast)

class TestForecastGenerator(unittest.TestCase):
    def setUp(self):
        self.db_config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "rakusensdatabase4"
        }
        self.script_dir = "/test/path"
        self.start_time = datetime(2025, 1, 1, 0, 0, 0)
        self.interval = timedelta(minutes=1)
        self.duration = timedelta(minutes=10)
        
        self.generator = ForecastGenerator(
            self.db_config, self.script_dir,
            self.start_time, self.interval, self.duration
        )
        self.generator.db_manager = MagicMock()
        self.generator.forecast_model = MagicMock()

    def test_generate_timestamps(self):
        timestamps = self.generator.generate_timestamps()
        self.assertEqual(len(timestamps), 11)

    def test_process_line_line4(self):
        self.generator.forecast_model.detect_sensors.return_value = [f"r{i:02d}" for i in range(1, 9)]
        self.generator.process_line("line4")
        self.assertEqual(self.generator.db_manager.store_forecasts.call_count, 8 * 11)

    def test_process_line_line5(self):
        self.generator.forecast_model.detect_sensors.return_value = [f"r{i:02d}" for i in range(1, 18)]
        self.generator.process_line("line5")
        self.assertEqual(self.generator.db_manager.store_forecasts.call_count, 17 * 11)

    def test_process_line_no_sensors(self):
        self.generator.forecast_model.detect_sensors.return_value = []
        self.generator.process_line("line4")
        self.generator.db_manager.get_connection.assert_not_called()

    def test_generate_and_store_forecasts(self):
        self.generator.process_line = MagicMock()
        self.generator.generate_and_store_forecasts()
        self.assertEqual(self.generator.process_line.call_count, 2)

if __name__ == '__main__':
    unittest.main(
        testRunner=unittest.TextTestRunner(
            resultclass=EmojiTestResult,
            verbosity=2
        )
    )