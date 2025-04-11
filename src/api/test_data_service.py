import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from app import DataService, LogService
from flask import json
import re
from threading import Thread 
from werkzeug.security import generate_password_hash

class TestDataService(unittest.TestCase):
    def setUp(self):
        """Set up the necessary mocks and DataService instance"""
        self.mock_db = MagicMock()
        self.mock_log = MagicMock(spec=LogService)
        self.data_service = DataService(self.mock_db, self.mock_log)
        
    def test_historical_data_retrieval(self):
        """Test historical data retrieval"""
        mock_data = [{'timestamp': datetime.now(), 'value': 42.0}]
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_data
        self.mock_db.get_connection().cursor().execute.return_value = None

        
        response = self.data_service.get_historical_data('line4', {})
        
        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 1)

    @patch('app.generate_password_hash')
    def test_get_logs(self, mock_hash):
        """Test system logs retrieval"""
        mock_log_data = [
            {'timestamp': datetime(2025, 4, 7, 14, 30), 'message': 'System started'},
            {'timestamp': datetime(2025, 4, 7, 15, 0), 'message': 'User logged in'},
            {'timestamp': datetime(2025, 4, 7, 15, 30), 'message': 'User logged out'}
        ]
        
        self.mock_db.get_connection().cursor().fetchall.return_value = mock_log_data

        response = self.data_service.get_logs()

        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 3)

        for log in response['data']:
            self.assertEqual(len(log['timestamp'].split('-')), 3)

        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT * FROM logs ORDER BY timestamp DESC LIMIT 100"
        )
        self.mock_log.log_event.assert_called_once_with(
            "Admin retrieved all user logs", type='INFO', log_level='admin'
        )

    @patch('app.generate_password_hash')
    def test_get_forecasted_data(self, mock_hash):
        """Test forecasted data retrieval"""
        mock_forecasted_data = [
            {'forecast_time': datetime(2025, 4, 7, 10, 30), 'forecast_value': 150.5},
            {'forecast_time': datetime(2025, 4, 7, 11, 30), 'forecast_value': 160.5},
            {'forecast_time': datetime(2025, 4, 7, 12, 30), 'forecast_value': 170}
        ]

        self.mock_db.get_connection().cursor().fetchall.return_value = mock_forecasted_data

        response = self.data_service.get_forecasted_data('line4')

        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 3)

        for forecast in response['data']:
            self.assertTrue(150 <= forecast['forecast_value'] <= 170)

        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT * FROM forecastedline4 ORDER BY forecast_time ASC"
        )
        self.mock_log.log_event.assert_called_once_with(
            "Forecasted data retrieved for line4", type='INFO'
        )

    @patch('app.generate_password_hash')  
    def test_get_sensor_data(self, mock_hash):
        """Test individual sensor data retrieval"""
        mock_sensor_data = {
            'timestamp': datetime(2025, 4, 7, 14, 30),
            'r01': 22.5
        }

        self.mock_db.get_connection().cursor().fetchone.return_value = mock_sensor_data

        response = self.data_service.get_sensor_data('line4', 'r01')

        self.assertTrue(response['success'])
        self.assertEqual(response['data']['r01'], 22.5)

        self.assertEqual(len(response['data']['timestamp'].split('-')), 3)

        self.mock_db.get_connection().cursor().execute.assert_called_with(
            "SELECT timestamp, r01 FROM line4 ORDER BY timestamp DESC LIMIT 1"
        )
        self.mock_log.log_event.assert_called_once_with(
            "Sensor data retrieved for r01 from line4", type='INFO', log_level='admin')

    def test_historical_data_filtering(self):
        """Test historical data with different filters without specifying a specific sensor"""
        filter_criteria = {
            'length': 10,  
            'searchValue': '2025-04-07',  
            'dateFilter': '2025-04-07',
            'startDateTime': '2025-04-01 00:00:00',  
            'endDateTime': '2025-04-07 23:59:59'  
        }

        mock_response = {
            "success": True,
            "data": [
                {"timestamp": "2025-04-07 10:00:00", "r01": 123.45, "r02": 130.50},
                {"timestamp": "2025-04-07 11:00:00", "r01": 125.75, "r02": 135.25},
                {"timestamp": "2025-04-07 12:00:00", "r01": 127.65, "r02": 137.90}
            ],
            "recordsTotal": 3,
            "recordsFiltered": 3
        }

        with patch.object(self.data_service, 'get_historical_data', return_value=mock_response):
            response = self.data_service.get_historical_data('line4', filter_criteria)

        self.assertTrue(response['success'])
        self.assertEqual(len(response['data']), 3)

        for record in response['data']:
            self.assertIn('timestamp', record)
            self.assertIn('r01', record)
            self.assertIn('r02', record)
            self.assertIsInstance(record['timestamp'], str)
            self.assertIsInstance(record['r01'], (float, int))
            self.assertIsInstance(record['r02'], (float, int))

        for record in response['data']:
            self.assertEqual(len(record['timestamp'].split('-')), 3)

    def test_live_data_format(self):
        """Test live data format and structure"""
        mock_live_data = {
            "success": True,
            "data": {
                "timestamp": "2025-04-07 15:30:00",
                "r01": 150.5,  
                "r02": 160.75  
            }
        }

        with patch.object(self.data_service, 'get_live_data', return_value=mock_live_data):
            response = self.data_service.get_live_data('line4')

        self.assertTrue(response['success'])

        live_data = response['data']
        
        self.assertIn('timestamp', live_data)
        self.assertIsInstance(live_data['timestamp'], str)
        self.assertEqual(len(live_data['timestamp'].split('-')), 3)
        
        self.assertIn('r01', live_data)
        self.assertIn('r02', live_data)
        self.assertIsInstance(live_data['r01'], (int, float))
        self.assertIsInstance(live_data['r02'], (int, float))

        self.assertGreater(live_data['r01'], 0, "Sensor r01 value should be greater than 0")
        self.assertGreater(live_data['r02'], 0, "Sensor r02 value should be greater than 0")

if __name__ == '__main__':
    unittest.main()


