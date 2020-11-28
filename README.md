# Capstone Project - Semantic-Aware Resource Characterization and Prediction

> This is the Official Github repo for the capstone project

Team Members:

1. Gerin
2. Nekhil
3. Joshua
4. Polina

## Coding Guidelines

* Most of the codebase is in Python. Let us try to use Python for most of our work unless required otherwise. This reduces mental overhead when context switching between different languages.

* Follow the Python PEP8 coding style guidelines. This ensures consisteny in the codebase. Major points to keep in mind:

        Snake case for variables: this_is_a_variable = 5

        Class names use camel case: ClassName

        Be descriptive with names: instead of x = 5 -- use number_of_machines = 5 etc.
        
* Try to use pure functions whenever possible, i.e when you have a function with some arguments do not modify the data passed in through the arguments directly instead return the output. In other words, if you'd like functions to be pure, then do not change the value of the input or any data that exists outside the function's scope. (FYI functions in python have arguments passed by reference)
