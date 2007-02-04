import doctest
import sys

def test(modname):
    mod = __import__(modname)
    failure, nb_test = doctest.testmod(mod)
    if failure:
        sys.exit(1)

def main():
    test("regex")
    test("op_regex")
    test("parser")

if __name__ == "__main__":
    main()

