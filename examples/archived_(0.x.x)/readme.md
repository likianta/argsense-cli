# Auto Test

We've added a fixture that automatically runs all examples in a quick through.

1. cd to project root.
2. pip install development requirements: `pip install -r requirements-dev.txt`
3. open a terminal

    - get help of fixture tool:

        ```sh
        py examples/fixture.py -h
        py examples/fixture.py test -h
        py examples/fixture.py auto-test-all -h
        ```

        ![](../.assets/examples/20221120140330.png)

    - test specific example:

        ```sh
        py examples/fixture.py test examples/hello_world.py
        ```

    - auto test all examples:

        ```sh
        py examples/fixture.py auto-test-all
        ```

Here is a screenshot of the auto test in action:

![](../.assets/examples/20221120141557.png)

# Index

If you want to read the examples, here is the suggested order to walk through:

1.  classic.py
    
    A quick guide through to the classic usages of `argsense` cli.

2.  advanced.py

    Fancy usages of `argsense` cli.

3.  errors.py
    
    Let's see what it would happen if we pass wrong command line arguments.

4.  seldomly_used.py

    Some edge features.
