import unittest
import sys
import os

def run_all_tests():
    # Add current directory to path so imports work
    sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/.."))
    
    loader = unittest.TestLoader()
    suite = loader.discover('tests')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if not result.wasSuccessful():
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()
