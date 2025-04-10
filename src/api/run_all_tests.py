import unittest
from unittest.runner import TextTestResult

# Custom TestResult class with emoji support
class EmojiTestResult(TextTestResult):
    def addSuccess(self, test):
        super().addSuccess(test)
        if self.showAll:  # Only if verbose mode is enabled
            self.stream.writeln(f"{test._testMethodName}: ✅ Passed!")
    
    def printErrors(self):
        super().printErrors()
        if self.dots:
            self.stream.writeln()  # New line after the dots
    
    def startTest(self, test):
        super().startTest(test)
        if self.showAll:
            self.stream.write(f"Running {test._testMethodName}... ")
            self.stream.flush()

# Import all the test modules
from test_flask_endpoints import TestFlaskEndpoints
from test_auth_service import TestAuthService
from test_admin_service import TestAdminService
from test_data_service import TestDataService
from test_simulation_service import TestSimulationService
from test_log_service import TestLogService
from test_database_manager import TestDatabaseManager

if __name__ == '__main__':
    # Create a test suite
    suite = unittest.TestSuite()

    # Add tests to the suite
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestFlaskEndpoints))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAuthService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestAdminService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDataService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestSimulationService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestLogService))
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(TestDatabaseManager))

    # Print the number of tests being run
    print(f"🧪 Total number of tests: {suite.countTestCases()}\n")

    # Run the tests with our custom runner
    runner = unittest.TextTestRunner(
        verbosity=2,  # Keep verbose output
        resultclass=EmojiTestResult
    )
    result = runner.run(suite)
    
    # Add summary emoji
    print("\n" + "="*50)
    if result.wasSuccessful():
        print(f"🎉 All {result.testsRun} tests passed!")
    else:
        print(f"🔥 {len(result.failures)} failures, {len(result.errors)} errors in {result.testsRun} tests")