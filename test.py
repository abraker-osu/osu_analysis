import unittest

# Beatmap reading test
from unit_tests.test_analysis import TestAnalysis
from unit_tests.test_mania_action_data import TestManiaActionData
from unit_tests.test_mania_score_data_press import TestManiaScoreDataPress
from unit_tests.test_mania_score_data import TestManiaScoreData


# Override function so that stdout output is not polluted with 
# the short descriptions it gets from commented out function 
# description text
unittest.TestCase.shortDescription = lambda x: None


# Thanks https://stackoverflow.com/questions/35930811/how-to-sort-unittest-testcases-properly
def suiteFactory(
        *testcases,
        testSorter   = None,
        suiteMaker   = unittest.makeSuite,
        newTestSuite = unittest.TestSuite
    ):
    """
    make a test suite from test cases, or generate test suites from test cases.
    *testcases     = TestCase subclasses to work on
    testSorter     = sort tests using this function over sorting by line number
    suiteMaker     = should quack like unittest.makeSuite.
    newTestSuite   = should quack like unittest.TestSuite.
    """

    if testSorter is None:
        ln         = lambda f:    getattr(tc, f).__code__.co_firstlineno
        testSorter = lambda a, b: ln(a) - ln(b)

    test_suite = newTestSuite()
    for tc in testcases:
        test_suite.addTest(suiteMaker(tc, sortUsing=testSorter))

    return test_suite


def caseFactory(
        scope        = globals().copy(),
        caseSorter   = lambda f: __import__("inspect").findsource(f)[1],
        caseSuperCls = unittest.TestCase,
        caseMatches  = __import__("re").compile("^Test")
    ):
    """
    get TestCase-y subclasses from frame "scope", filtering name and attribs
    scope        = iterable to use for a frame; preferably a hashable (dictionary).
    caseMatches  = regex to match function names against; blank matches every TestCase subclass
    caseSuperCls = superclass of test cases; unittest.TestCase by default
    caseSorter   = sort test cases using this function over sorting by line number
    """

    import re

    return sorted(
        [
            scope[obj] for obj in scope
                if re.match(caseMatches, obj) and issubclass(scope[obj], caseSuperCls)
        ],
        key=caseSorter
    )


if __name__ == '__main__':
    cases = suiteFactory(*caseFactory())
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(cases)