import unittest

# Import all the test modules
from test_flask_endpoints import TestFlaskEndpoints
from test_auth_service import TestAuthService
from test_admin_service import TestAdminService
from test_data_service import TestDataService
from test_simulation_service import TestSimulationService
from test_log_service import TestLogService

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()

    # Add tests to the suite using loadTestsFromTestCase instead of makeSuite
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFlaskEndpoints))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuthService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdminService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSimulationService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLogService))

    # Print the number of tests being run
    print(f"Total number of tests: {suite.countTestCases()}")

    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
